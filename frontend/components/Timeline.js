import React from 'react'
import { Box, Typography, Paper, Tooltip } from '@mui/material'
import AccessTimeIcon from '@mui/icons-material/AccessTime'

const Timeline = ({ duration, cuts, currentTime, onSeek }) => {
  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const timestampToSeconds = (timestamp) => {
    const parts = timestamp.split(':')
    if (parts.length === 3) {
      const [hours, minutes, seconds] = parts.map(Number)
      return hours * 3600 + minutes * 60 + seconds
    } else if (parts.length === 2) {
      const [minutes, seconds] = parts.map(Number)
      return minutes * 60 + seconds
    }
    return Number(timestamp)
  }

  const handleClick = (e) => {
    if (onSeek && duration > 0) {
      const rect = e.currentTarget.getBoundingClientRect()
      const x = e.clientX - rect.left
      const percentage = x / rect.width
      const seekTime = percentage * duration
      onSeek(seekTime)
    }
  }

  const playheadPosition = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <Paper elevation={2} className="timeline-container">
      <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <AccessTimeIcon sx={{ fontSize: 20 }} />
        <Typography variant="subtitle1" fontWeight="medium">
          Zaman Çizelgesi
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ ml: 'auto' }}>
          {formatTime(currentTime)} / {formatTime(duration)}
        </Typography>
      </Box>

      <Box
        className="timeline"
        onClick={handleClick}
        sx={{ position: 'relative' }}
      >
        {/* Kesim segmentleri */}
        {cuts.map((cut, index) => {
          const startSeconds = timestampToSeconds(cut.start)
          const endSeconds = timestampToSeconds(cut.end)
          const left = (startSeconds / duration) * 100
          const width = ((endSeconds - startSeconds) / duration) * 100

          return (
            <Tooltip
              key={index}
              title={`${cut.start} - ${cut.end}`}
              placement="top"
              arrow
            >
              <Box
                className="timeline-segment"
                sx={{
                  left: `${left}%`,
                  width: `${width}%`,
                }}
              />
            </Tooltip>
          )
        })}

        {/* Oynatma kafası */}
        <Box
          className="timeline-playhead"
          sx={{
            left: `${playheadPosition}%`,
          }}
        />
      </Box>

      {cuts.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="textSecondary">
            Toplam {cuts.length} kesim seçildi
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Mavi alanlar kesilecek bölümleri gösterir
          </Typography>
        </Box>
      )}
    </Paper>
  )
}

export default Timeline