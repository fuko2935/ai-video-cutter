import React, { useRef, useEffect } from 'react'
import ReactPlayer from 'react-player'
import { Box, IconButton, Slider, Typography } from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import PauseIcon from '@mui/icons-material/Pause'
import VolumeUpIcon from '@mui/icons-material/VolumeUp'
import VolumeOffIcon from '@mui/icons-material/VolumeOff'
import FullscreenIcon from '@mui/icons-material/Fullscreen'

const VideoPlayer = ({
  url,
  playing,
  onPlayPause,
  onProgress,
  onDuration,
  onSeek,
  currentTime
}) => {
  const playerRef = useRef(null)
  const [volume, setVolume] = React.useState(1)
  const [muted, setMuted] = React.useState(false)

  const handleSeek = (newTime) => {
    if (playerRef.current) {
      playerRef.current.seekTo(newTime)
      if (onSeek) {
        onSeek(newTime)
      }
    }
  }

  const handleFullscreen = () => {
    const playerElement = playerRef.current?.wrapper
    if (playerElement?.requestFullscreen) {
      playerElement.requestFullscreen()
    }
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Dışarıdan seek geldiğinde
  useEffect(() => {
    if (currentTime !== undefined && playerRef.current) {
      const currentPlayerTime = playerRef.current.getCurrentTime()
      if (Math.abs(currentPlayerTime - currentTime) > 1) {
        playerRef.current.seekTo(currentTime)
      }
    }
  }, [currentTime])

  return (
    <Box className="video-container">
      <Box sx={{ position: 'relative', paddingTop: '56.25%' /* 16:9 */ }}>
        <ReactPlayer
          ref={playerRef}
          url={url}
          playing={playing}
          volume={volume}
          muted={muted}
          onProgress={onProgress}
          onDuration={onDuration}
          width="100%"
          height="100%"
          style={{
            position: 'absolute',
            top: 0,
            left: 0
          }}
        />
      </Box>

      {/* Video kontrolleri */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          p: 2,
          bgcolor: 'rgba(0, 0, 0, 0.8)',
          color: 'white'
        }}
      >
        <IconButton
          color="inherit"
          onClick={onPlayPause}
          size="large"
        >
          {playing ? <PauseIcon /> : <PlayArrowIcon />}
        </IconButton>

        <Typography variant="body2" sx={{ minWidth: 80 }}>
          {formatTime(currentTime || 0)}
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <IconButton
            color="inherit"
            onClick={() => setMuted(!muted)}
            size="small"
          >
            {muted ? <VolumeOffIcon /> : <VolumeUpIcon />}
          </IconButton>
          
          <Slider
            value={muted ? 0 : volume}
            onChange={(e, newValue) => {
              setVolume(newValue)
              setMuted(false)
            }}
            min={0}
            max={1}
            step={0.1}
            sx={{
              width: 80,
              color: 'white',
              '& .MuiSlider-thumb': {
                width: 12,
                height: 12
              }
            }}
          />
        </Box>

        <IconButton
          color="inherit"
          onClick={handleFullscreen}
          size="small"
          sx={{ ml: 'auto' }}
        >
          <FullscreenIcon />
        </IconButton>
      </Box>
    </Box>
  )
}

export default VideoPlayer