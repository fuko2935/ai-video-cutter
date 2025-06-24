import React, { useState, useRef, useEffect } from 'react'
import {
  Box,
  TextField,
  IconButton,
  Paper,
  Typography,
  Chip,
  CircularProgress
} from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import PersonIcon from '@mui/icons-material/Person'

const PRESET_PROMPTS = [
  'En komik anları bul',
  'Sessiz yerleri at',
  'Sadece konuşmaların olduğu yerleri kes',
  'En heyecanlı 5 anı bul',
  'İlk 30 saniyeyi kes',
  'Son 1 dakikayı al'
]

const ChatInterface = ({ messages, onSendMessage, isLoading, disabled }) => {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = () => {
    if (inputValue.trim() && !isLoading && !disabled) {
      onSendMessage(inputValue.trim())
      setInputValue('')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handlePresetClick = (prompt) => {
    if (!isLoading && !disabled) {
      onSendMessage(prompt)
    }
  }

  return (
    <Paper elevation={2} className="chat-container">
      <Box className="chat-messages">
        {messages.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              gap: 2
            }}
          >
            <SmartToyIcon sx={{ fontSize: 48, color: 'text.secondary' }} />
            <Typography variant="h6" color="textSecondary">
              Klip Asistanı'na hoş geldiniz!
            </Typography>
            <Typography variant="body2" color="textSecondary" textAlign="center">
              Videolarınızı nasıl kesmek istediğinizi doğal bir dille anlatın.
            </Typography>
          </Box>
        ) : (
          messages.map((msg, index) => (
            <Box
              key={index}
              className={`chat-message ${msg.type}`}
              sx={{
                display: 'flex',
                gap: 1.5,
                alignItems: 'flex-start'
              }}
            >
              <Box sx={{ mt: 0.5 }}>
                {msg.type === 'user' ? (
                  <PersonIcon sx={{ fontSize: 20 }} />
                ) : (
                  <SmartToyIcon sx={{ fontSize: 20 }} />
                )}
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography variant="body1">{msg.text}</Typography>
                {msg.cuts && msg.cuts.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="textSecondary">
                      {msg.cuts.length} kesim önerisi
                    </Typography>
                  </Box>
                )}
              </Box>
            </Box>
          ))
        )}
        
        {isLoading && (
          <Box className="chat-message ai" sx={{ display: 'flex', gap: 1 }}>
            <CircularProgress size={16} />
            <Typography variant="body2">Analiz ediliyor...</Typography>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>

      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Box className="prompt-buttons">
          {PRESET_PROMPTS.map((prompt, index) => (
            <Chip
              key={index}
              label={prompt}
              onClick={() => handlePresetClick(prompt)}
              clickable
              disabled={isLoading || disabled}
              size="small"
              variant="outlined"
            />
          ))}
        </Box>
      </Box>

      <Box className="chat-input-container">
        <TextField
          fullWidth
          multiline
          maxRows={3}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ne yapmak istersiniz?"
          disabled={isLoading || disabled}
          size="small"
          sx={{ flex: 1 }}
        />
        <IconButton
          color="primary"
          onClick={handleSend}
          disabled={!inputValue.trim() || isLoading || disabled}
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Paper>
  )
}

export default ChatInterface