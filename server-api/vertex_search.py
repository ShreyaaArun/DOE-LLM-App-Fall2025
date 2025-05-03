import os
from google.cloud import discoveryengine_v1beta as discoveryengine

class VertexSearchClient:
    # Updated the default data_store_id to the correct one
    def __init__(self, project_id=None, location="global", data_store_id="doe-test-lol_1745604486056"):
        """Initializes the client using Application Default Credentials."""
        # Try to get project_id from environment if not provided
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        if not self.project_id:
            # You might want to fetch it using gcloud config get-value project if needed
            # Or raise an error if it's absolutely required and not found
            raise ValueError("Google Cloud Project ID not provided and GOOGLE_CLOUD_PROJECT env var not set.")
            
        self.location = location
        self.data_store_id = data_store_id
        
        # Initialize the Discovery Engine SearchServiceClient
        # This automatically uses Application Default Credentials (ADC)
        self.client = discoveryengine.SearchServiceClient()

        # Construct the Serving Config path
        self.serving_config = self.client.serving_config_path(
            project=self.project_id,
            location=self.location,
            data_store=self.data_store_id,
            serving_config="default_config",  # Use 'default_config' unless you created a custom one
        )
        print(f"VertexSearchClient initialized for project '{self.project_id}', location '{self.location}', data store '{self.data_store_id}'")
        print(f"Using serving config: {self.serving_config}")

    def search(self, query, page_size=5):
        """Performs a search using the Discovery Engine client library."""
        request_payload = discoveryengine.SearchRequest(
            serving_config=self.serving_config,
            query=query,
            page_size=page_size,
            query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
                condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
            ),
            spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO,
            ),
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                    return_snippet=True
                ),
                summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                    summary_result_count=3, # Request summaries for top 3 results
                    include_citations=True,
                )
            )
            # Add language_codes=["en"] if needed
        )

        print(f"Sending search request to Discovery Engine for query: '{query}'")
        response = self.client.search(request=request_payload)
        print("Received response from Discovery Engine.")

        # Format the results similarly to before, extracting from the response object
        results = []
        summary = response.summary.summary_text if response.summary else "No summary available."

        for search_result in response.results:
            doc = search_result.document
            # Extract fields safely using .get()
            title = doc.derived_struct_data.get("title", "No Title")
            link = doc.derived_struct_data.get("link", "#")
            snippet_info = doc.derived_struct_data.get("snippets", [{}])[0]
            snippet = snippet_info.get("snippet", "No snippet available.")
            
            results.append({
                "id": doc.id,
                "title": title,
                "link": link,
                "snippet": snippet,
            })
            
        print(f"Formatted {len(results)} results. Summary available: {bool(summary)}")
        return {"summary": summary, "results": results}

    # Note: The search_and_answer method using a separate :answer call might 
    # not be the standard way with this library. The summary is often included 
    # directly in the search response if requested via content_search_spec.
    # We will rely on the summary from the search method for now.
    # def search_and_answer(self, query, page_size=10):
    #     # This method would need significant changes to work with the client library
    #     # or might be replaced entirely by using the summary_spec in search().
    #     pass 

# Example usage (for testing if needed):
# if __name__ == '__main__':
#     try:
#         # Make sure GOOGLE_CLOUD_PROJECT is set in your environment
#         client = VertexSearchClient(data_store_id='YOUR_DATA_STORE_ID') # Replace with your actual data store ID
#         search_results = client.search("What is combinatorial testing?")
#         print("\nSearch Results:")
#         import json
#         print(json.dumps(search_results, indent=2))
#     except Exception as e:
#         print(f"Error during example usage: {e}")
#         traceback.print_exc()