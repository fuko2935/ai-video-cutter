import React, { useState, useEffect } from 'react'
import Head from 'next/head'
import {
  Container,
  Grid,
  Paper,
  Typography,
  Button,
  Alert,
  Box,
  Snackbar,
  LinearProgress
} from '@mui/material'
import ContentCutIcon from '@mui/icons-material/ContentCut'
import DownloadIcon from '@mui/icons-material/Download'
import axios from 'axios'

import VideoUploader from '../components/VideoUploader'
import VideoPlayer from '../components/VideoPlayer'
import ChatInterface from '../components/ChatInterface'
import Timeline from '../components/Timeline'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

export default function Home() {
  // State tanımlamaları
  const [videoFile, setVideoFile] = useState(null)
  const [videoUrl, setVideoUrl] = useState(null)
  const [videoId, setVideoId] = useState(null)
  const [videoDuration, setVideoDuration] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState(null)
  
  // Player state
  const [playing, setPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  
  // Chat state
  const [messages, setMessages] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentCuts, setCurrentCuts] = useState([])
  
  // Finalize state
  const [isFinalizing, setIsFinalizing] = useState(false)
  const [downloadUrl, setDownloadUrl] = useState(null)
  
  // Snackbar state
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' })

  // Video durumunu kontrol et
  useEffect(() => {
    if (videoId && !uploadStatus?.includes('ready')) {
      const interval = setInterval(async () => {
        try {
          const response = await axios.get(`${API_URL}/api/status/${videoId}`)
          const { status, message } = response.data
          
          if (status === 'ready') {
            setUploadStatus('Video hazır!')
            clearInterval(interval)
          } else if (status === 'error') {
            setUploadStatus(`Hata: ${message}`)
            clearInterval(interval)
          }
        } catch (error) {
          console.error('Status check error:', error)
        }
      }, 2000)
      
      return () => clearInterval(interval)
    }
  }, [videoId, uploadStatus])

  // Video yükleme
  const handleVideoUpload = async (file) => {
    setIsUploading(true)
    setUploadStatus('Video yükleniyor...')
    
    const formData = new FormData()
    formData.append('video', file)
    
    try {
      const response = await axios.post(`${API_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      const { video_id } = response.data
      setVideoId(video_id)
      setVideoFile(file)
      setVideoUrl(URL.createObjectURL(file))
      setUploadStatus('Video işleniyor...')
      
      setSnackbar({
        open: true,
        message: 'Video başarıyla yüklendi!',
        severity: 'success'
      })
    } catch (error) {
      console.error('Upload error:', error)
      setUploadStatus('Yükleme hatası!')
      setSnackbar({
        open: true,
        message: 'Video yüklenirken hata oluştu!',
        severity: 'error'
      })
    } finally {
      setIsUploading(false)
    }
  }

  // Chat mesajı gönder
  const handleSendMessage = async (message) => {
    if (!videoId) return
    
    // Kullanıcı mesajını ekle
    setMessages(prev => [...prev, { type: 'user', text: message }])
    setIsProcessing(true)
    
    try {
      const response = await axios.post(`${API_URL}/api/chat/${videoId}`, {
        prompt: message
      })
      
      const { cuts, message: aiMessage } = response.data
      
      // AI yanıtını ekle
      setMessages(prev => [...prev, {
        type: 'ai',
        text: aiMessage,
        cuts: cuts
      }])
      
      // Kesimleri güncelle
      if (cuts && cuts.length > 0) {
        setCurrentCuts(cuts)
      }
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, {
        type: 'ai',
        text: 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.'
      }])
    } finally {
      setIsProcessing(false)
    }
  }

  // Video birleştirme
  const handleFinalize = async () => {
    if (!videoId || currentCuts.length === 0) return
    
    setIsFinalizing(true)
    
    try {
      // Birleştirme işlemini başlat
      const response = await axios.post(`${API_URL}/api/finalize`, {
        video_id: videoId,
        cuts: currentCuts
      })
      
      setSnackbar({
        open: true,
        message: 'Video işleniyor, lütfen bekleyin...',
        severity: 'info'
      })
      
      // Durum kontrolü
      const checkInterval = setInterval(async () => {
        try {
          const statusResponse = await axios.get(`${API_URL}/api/status/${videoId}`)
          const { status } = statusResponse.data
          
          if (status === 'completed') {
            clearInterval(checkInterval)
            setDownloadUrl(`${API_URL}/api/download/${videoId}`)
            setSnackbar({
              open: true,
              message: 'Video hazır!',
              severity: 'success'
            })
            setIsFinalizing(false)
          } else if (status === 'error') {
            clearInterval(checkInterval)
            setSnackbar({
              open: true,
              message: 'Video işlenirken hata oluştu!',
              severity: 'error'
            })
            setIsFinalizing(false)
          }
        } catch (error) {
          console.error('Status check error:', error)
        }
      }, 2000)
      
    } catch (error) {
      console.error('Finalize error:', error)
      setSnackbar({
        open: true,
        message: 'İşlem başlatılırken hata oluştu!',
        severity: 'error'
      })
      setIsFinalizing(false)
    }
  }

  return (
    <>
      <Head>
        <title>AI Video Kesici - Akıllı Video Düzenleme</title>
        <meta name="description" content="AI destekli video kesme ve düzenleme aracı" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          AI Video Kesici
        </Typography>
        <Typography variant="h6" color="textSecondary" align="center" sx={{ mb: 4 }}>
          Videolarınızı doğal dil komutlarıyla kesin ve düzenleyin
        </Typography>

        {!videoFile ? (
          <Paper elevation={3} sx={{ p: 4 }}>
            <VideoUploader onUpload={handleVideoUpload} isUploading={isUploading} />
            {uploadStatus && (
              <Alert severity="info" sx={{ mt: 2 }}>
                {uploadStatus}
              </Alert>
            )}
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {/* Sol taraf - Video ve Timeline */}
            <Grid item xs={12} md={7}>
              <Paper elevation={3} sx={{ overflow: 'hidden' }}>
                <VideoPlayer
                  url={videoUrl}
                  playing={playing}
                  onPlayPause={() => setPlaying(!playing)}
                  onProgress={({ playedSeconds }) => setCurrentTime(playedSeconds)}
                  onDuration={setVideoDuration}
                  onSeek={setCurrentTime}
                  currentTime={currentTime}
                />
              </Paper>
              
              <Box sx={{ mt: 2 }}>
                <Timeline
                  duration={videoDuration}
                  cuts={currentCuts}
                  currentTime={currentTime}
                  onSeek={(time) => setCurrentTime(time)}
                />
              </Box>
              
              {/* Aksiyon butonları */}
              <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  startIcon={<ContentCutIcon />}
                  onClick={handleFinalize}
                  disabled={currentCuts.length === 0 || isFinalizing}
                  fullWidth
                >
                  {isFinalizing ? 'İşleniyor...' : 'Kes ve Birleştir'}
                </Button>
                
                {downloadUrl && (
                  <Button
                    variant="contained"
                    color="success"
                    size="large"
                    startIcon={<DownloadIcon />}
                    href={downloadUrl}
                    download
                    fullWidth
                  >
                    İndir
                  </Button>
                )}
              </Box>
              
              {isFinalizing && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress />
                  <Typography variant="body2" color="textSecondary" align="center" sx={{ mt: 1 }}>
                    Video işleniyor, bu birkaç dakika sürebilir...
                  </Typography>
                </Box>
              )}
            </Grid>

            {/* Sağ taraf - Chat */}
            <Grid item xs={12} md={5}>
              <ChatInterface
                messages={messages}
                onSendMessage={handleSendMessage}
                isLoading={isProcessing}
                disabled={!videoId || uploadStatus !== 'Video hazır!'}
              />
              
              {uploadStatus && uploadStatus !== 'Video hazır!' && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  {uploadStatus}
                </Alert>
              )}
            </Grid>
          </Grid>
        )}
      </Container>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  )
}