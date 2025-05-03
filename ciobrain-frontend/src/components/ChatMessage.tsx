import React from 'react';
import { motion } from 'framer-motion';

interface Evidence {
  quote: string;
  source: string;
  page: string;
  supports: string;
}

interface ChatMessageProps {
  message: string;
  evidence?: Evidence[];
  isUser: boolean;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, evidence, isUser }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div className={`relative max-w-[80%] ${isUser ? 'order-1' : 'order-2'}`}>
        <div
          className={`rounded-lg px-4 py-2 ${
            isUser
              ? 'bg-gradient-to-r from-violet-600 to-indigo-800 text-white'
              : 'bg-gray-800 text-gray-200'
          }`}
        >
          <p className="text-sm">{message}</p>
          {evidence && evidence.length > 0 && (
            <div className="mt-2 border-t border-gray-600 pt-2">
              <h4 className="text-xs font-semibold mb-1">Evidence:</h4>
              <ul className="list-disc list-inside space-y-1">
                {evidence.map((item, index) => (
                  <li key={index} className="text-xs">
                    "{item.quote}" (Source: {item.source}, Page: {item.page})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default ChatMessage;