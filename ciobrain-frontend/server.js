const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');
const fetch = require('node-fetch');

const app = express();
const PORT = process.env.PORT || 5001;

// Middleware
app.use(cors());
app.use(express.json());

// Get Google Cloud access token using gcloud CLI
const getAccessToken = () => {
  return new Promise((resolve, reject) => {
    exec('gcloud auth print-access-token', (error, stdout, stderr) => {
      if (error) {
        console.error(`Error getting access token: ${error.message}`);
        return reject(error);
      }
      if (stderr) {
        console.error(`stderr: ${stderr}`);
        return reject(new Error(stderr));
      }
      resolve(stdout.trim());
    });
  });
};

// Define the base URL for the Google Cloud Search API
const API_BASE_URL = 'https://discoveryengine.googleapis.com/v1alpha/projects/341304510567/locations/global/collections/default_collection/engines/doe-test_1745604392169/servingConfigs/default_search';

// API route for search
app.post('/api/search', async (req, res) => {
  try {
    const { query, newSession = true } = req.body;
    
    if (!query) {
      return res.status(400).json({ error: 'Query is required' });
    }
    
    // Get access token
    const accessToken = await getAccessToken();
    
    // Make request to Google Cloud Search API
    const response = await fetch(`${API_BASE_URL}:search`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query,
        pageSize: 10,
        queryExpansionSpec: { condition: 'AUTO' },
        spellCorrectionSpec: { mode: 'AUTO' },
        languageCode: 'en-US',
        contentSearchSpec: {
          extractiveContentSpec: {
            maxExtractiveAnswerCount: 1,
            maxExtractiveSegmentCount: 1,
          }
        },
        session: newSession ? '-' : req.body.sessionId // '-' creates a new session
      }),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Google Search API Error:', errorText);
      return res.status(response.status).json({
        error: `Error from Google Search API: ${response.statusText}`,
        details: errorText
      });
    }
    
    const data = await response.json();
    
    // Extract and return relevant information
    const results = data.results || [];
    const sessionInfo = {
      queryId: data.queryId,
      sessionId: data.session
    };
    
    res.json({
      results,
      sessionInfo
    });
  } catch (error) {
    console.error('Search API error:', error);
    res.status(500).json({ error: 'Failed to search', details: error.message });
  }
});

// API route for generating answers
app.post('/api/generate-answer', async (req, res) => {
  try {
    const { queryId, sessionId } = req.body;
    
    if (!queryId || !sessionId) {
      return res.status(400).json({ error: 'QueryId and SessionId are required' });
    }
    
    // Get access token
    const accessToken = await getAccessToken();
    
    // Make request to Google Cloud Answer API
    const response = await fetch(`${API_BASE_URL}:answer`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: {
          text: "", // Empty because we're using queryId
          queryId: queryId
        },
        session: sessionId,
        relatedQuestionsSpec: { enable: true },
        answerGenerationSpec: {
          ignoreAdversarialQuery: true,
          ignoreNonAnswerSeekingQuery: false,
          ignoreLowRelevance: false
        }
      }),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Google Answer API Error:', errorText);
      return res.status(response.status).json({
        error: `Error from Google Answer API: ${response.statusText}`,
        details: errorText
      });
    }
    
    const data = await response.json();
    
    res.json({
      answer: data.answer || null,
      relatedQuestions: data.relatedQuestions || []
    });
  } catch (error) {
    console.error('Generate Answer API error:', error);
    res.status(500).json({ error: 'Failed to generate answer', details: error.message });
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
}); 