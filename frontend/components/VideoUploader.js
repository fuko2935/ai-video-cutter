import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Box, Typography, CircularProgress } from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import VideocamIcon from '@mui/icons-material/Videocam'

const VideoUploader = ({ onUpload, isUploading }) => {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onUpload(acceptedFiles[0])
    }
  }, [onUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    },
    maxFiles: 1,
    disabled: isUploading
  })

  return (
    <Box
      {...getRootProps()}
      className={`upload-zone ${isDragActive ? 'active' : ''}`}
      sx={{
        minHeight: 300,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
        opacity: isUploading ? 0.6 : 1,
        pointerEvents: isUploading ? 'none' : 'auto'
      }}
    >
      <input {...getInputProps()} />
      
      {isUploading ? (
        <>
          <CircularProgress size={48} />
          <Typography variant="h6" color="textSecondary">
            Video yükleniyor...
          </Typography>
        </>
      ) : (
        <>
          {isDragActive ? (
            <CloudUploadIcon sx={{ fontSize: 64, color: 'primary.main' }} />
          ) : (
            <VideocamIcon sx={{ fontSize: 64, color: 'text.secondary' }} />
          )}
          
          <Typography variant="h6" color="textSecondary">
            {isDragActive
              ? 'Videoyu buraya bırakın'
              : 'Video yüklemek için tıklayın veya sürükleyin'}
          </Typography>
          
          <Typography variant="body2" color="textSecondary">
            Desteklenen formatlar: MP4, AVI, MOV, MKV, WEBM
          </Typography>
          
          <Typography variant="caption" color="textSecondary">
            Maksimum dosya boyutu: 500MB
          </Typography>
        </>
      )}
    </Box>
  )
}

export default VideoUploader