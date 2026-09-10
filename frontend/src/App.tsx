import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import MapComponent from './components/MapComponent';
import ChatPanel from './components/ChatPanel';
import ConditionsPanel from './components/ConditionsPanel';
import './App.css';

function App() {
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [conditions, setConditions] = useState<any>(null);
  const [riskAssessment, setRiskAssessment] = useState<any>(null);
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleSendMessage = async (message: string) => {
    setLoading(true);
    try {
      const response = await axios.post(`${apiUrl}/api/chat`, {
        session_id: `session-${Date.now()}`,
        user_message: message
      });
      
      setMessages(prev => [...prev, {
        type: 'user',
        content: message
      }, {
        type: 'assistant',
        content: response.data.response,
        risk_assessment: response.data.risk_assessment,
        marine_data: response.data.marine_data
      }]);
      
      setRiskAssessment(response.data.risk_assessment);
      setConditions(response.data.marine_data);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        type: 'error',
        content: 'Error processing request'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>SAPTHA SAGARA</h1>
        <p>Agentic Marine Intelligence Platform</p>
      </header>
      
      <div className="main-layout">
        <div className="left-panel">
          <ChatPanel 
            messages={messages} 
            onSendMessage={handleSendMessage}
            loading={loading}
          />
        </div>
        
        <div className="center-panel">
          <MapComponent />
        </div>
        
        <div className="right-panel">
          <ConditionsPanel 
            riskAssessment={riskAssessment}
            conditions={conditions}
          />
        </div>
      </div>
    </div>
  );
}

export default App;