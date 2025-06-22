"""
GLaDOS Vocoder Module

Applies audio effects to make TTS sound like GLaDOS from Portal.
Optimized for Raspberry Pi with efficient processing algorithms.
"""

import os
import numpy as np
import scipy.signal
from scipy.io import wavfile
import soundfile as sf
from typing import Optional, Tuple
import logging


class GLaDOSVocoder:
    """
    GLaDOS voice effect processor.
    
    Applies robotic/mechanical effects to make any TTS sound like GLaDOS:
    - Pitch shifting
    - Formant manipulation
    - Robotic resonance
    - Slight distortion
    - Echo/reverb effects
    """
    
    def __init__(self):
        self.sample_rate = 22050  # Standard rate for efficient processing
        
        # GLaDOS effect parameters (optimized for Pi)
        self.pitch_shift_semitones = -2  # Lower pitch slightly
        self.formant_shift = 0.85        # Shift formants down
        self.robotic_intensity = 0.3     # Robotic effect strength
        self.echo_delay_ms = 50          # Echo delay
        self.echo_decay = 0.2            # Echo volume decay
        self.distortion_amount = 0.1     # Subtle distortion
        
    def apply_glados_effect(self, input_file: str, output_file: Optional[str] = None) -> Optional[str]:
        """
        Apply GLaDOS voice effects to audio file.
        
        Args:
            input_file: Input audio file path
            output_file: Output file path (auto-generated if None)
            
        Returns:
            Output file path if successful, None otherwise
        """
        try:
            # Check if input file exists and is not empty
            if not os.path.exists(input_file):
                logging.error(f"Input file does not exist: {input_file}")
                return None
            
            if os.path.getsize(input_file) == 0:
                logging.error(f"Input file is empty: {input_file}")
                return None
            
            # Load audio
            audio_data, original_sr = sf.read(input_file)
            
            # Check if audio data is valid
            if audio_data is None or len(audio_data) == 0:
                logging.error(f"No audio data found in file: {input_file}")
                return None
            
            # Ensure mono audio
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Check if we have valid audio after conversion
            if len(audio_data) == 0:
                logging.error("Audio data is empty after processing")
                return None
            
            # Resample if necessary
            if original_sr != self.sample_rate:
                audio_data = self._resample_audio(audio_data, original_sr, self.sample_rate)
            
            # Final check before processing
            if len(audio_data) == 0:
                logging.error("Audio data is empty after resampling")
                return None
            
            # Apply GLaDOS effects
            processed_audio = self._apply_effects_pipeline(audio_data)
            
            # Check if processing succeeded
            if processed_audio is None or len(processed_audio) == 0:
                logging.error("Audio processing failed or resulted in empty audio")
                return None
            
            # Generate output filename if not provided
            if output_file is None:
                base_name = os.path.splitext(input_file)[0]
                output_file = f"{base_name}_glados.wav"
            
            # Save processed audio
            sf.write(output_file, processed_audio, self.sample_rate)
            
            logging.info(f"GLaDOS effect applied: {input_file} -> {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"GLaDOS effect failed: {e}")
            return None
    
    def _resample_audio(self, audio: np.ndarray, original_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate"""
        if original_sr == target_sr:
            return audio
        
        if len(audio) == 0:
            return audio
        
        # Calculate resampling ratio
        ratio = target_sr / original_sr
        new_length = int(len(audio) * ratio)
        
        if new_length <= 0:
            logging.warning("Resampling resulted in zero-length audio")
            return audio
        
        # Use scipy's resample for efficient resampling
        return scipy.signal.resample(audio, new_length)
    
    def _apply_effects_pipeline(self, audio: np.ndarray) -> np.ndarray:
        """Apply the complete GLaDOS effects pipeline"""
        if len(audio) == 0:
            logging.warning("Cannot apply effects to empty audio")
            return audio
        
        try:
            # 1. Normalize input
            audio = self._normalize_audio(audio)
            if len(audio) == 0:
                return audio
            
            # 2. Apply pitch shifting
            audio = self._pitch_shift(audio, self.pitch_shift_semitones)
            if len(audio) == 0:
                return audio
            
            # 3. Apply formant shifting
            audio = self._formant_shift(audio, self.formant_shift)
            if len(audio) == 0:
                return audio
            
            # 4. Add robotic resonance
            audio = self._add_robotic_resonance(audio, self.robotic_intensity)
            if len(audio) == 0:
                return audio
            
            # 5. Apply subtle distortion
            audio = self._apply_distortion(audio, self.distortion_amount)
            if len(audio) == 0:
                return audio
            
            # 6. Add echo effect
            audio = self._add_echo(audio, self.echo_delay_ms, self.echo_decay)
            if len(audio) == 0:
                return audio
            
            # 7. Final normalization
            audio = self._normalize_audio(audio)
            
            return audio
            
        except Exception as e:
            logging.error(f"Error in effects pipeline: {e}")
            return audio  # Return original audio if processing fails
    
    def _normalize_audio(self, audio: np.ndarray, target_level: float = 0.9) -> np.ndarray:
        """Normalize audio to target level"""
        if len(audio) == 0:
            return audio
        
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio * (target_level / max_val)
        return audio
    
    def _pitch_shift(self, audio: np.ndarray, semitones: float) -> np.ndarray:
        """
        Pitch shift using time-domain method (efficient for Pi).
        This is a simplified pitch shifting - not perfect but fast.
        """
        if semitones == 0 or len(audio) == 0:
            return audio
        
        try:
            # Calculate pitch ratio
            pitch_ratio = 2 ** (semitones / 12.0)
            
            # Simple pitch shifting using interpolation
            indices = np.arange(0, len(audio), pitch_ratio)
            indices = indices[indices < len(audio)]
            
            if len(indices) == 0:
                return audio
            
            # Interpolate
            shifted_audio = np.interp(indices, np.arange(len(audio)), audio)
            
            # Pad or trim to original length
            if len(shifted_audio) < len(audio):
                shifted_audio = np.pad(shifted_audio, (0, len(audio) - len(shifted_audio)))
            else:
                shifted_audio = shifted_audio[:len(audio)]
            
            return shifted_audio
            
        except Exception as e:
            logging.warning(f"Pitch shifting failed: {e}")
            return audio
    
    def _formant_shift(self, audio: np.ndarray, shift_ratio: float) -> np.ndarray:
        """
        Simple formant shifting using spectral manipulation.
        Simplified version for efficiency on Raspberry Pi.
        """
        if shift_ratio == 1.0 or len(audio) == 0:
            return audio
        
        try:
            # Apply FFT
            fft_data = np.fft.fft(audio)
            freqs = np.fft.fftfreq(len(audio), 1/self.sample_rate)
            
            # Shift formants by modifying the spectrum
            shifted_fft = np.zeros_like(fft_data)
            
            for i, freq in enumerate(freqs[:len(freqs)//2]):
                if freq > 0:
                    new_freq = freq * shift_ratio
                    new_idx = int(new_freq * len(audio) / self.sample_rate)
                    if 0 <= new_idx < len(freqs)//2:
                        shifted_fft[new_idx] = fft_data[i]
                        shifted_fft[-(new_idx+1)] = fft_data[-(i+1)]  # Mirror for negative frequencies
            
            # Convert back to time domain
            shifted_audio = np.real(np.fft.ifft(shifted_fft))
            
            return shifted_audio
            
        except Exception as e:
            logging.warning(f"Formant shifting failed: {e}")
            return audio
    
    def _add_robotic_resonance(self, audio: np.ndarray, intensity: float) -> np.ndarray:
        """Add robotic resonance using ring modulation"""
        if intensity == 0 or len(audio) == 0:
            return audio
        
        try:
            # Create carrier wave (robotic frequency)
            carrier_freq = 120  # Hz - typical robotic frequency
            t = np.linspace(0, len(audio) / self.sample_rate, len(audio))
            carrier = np.sin(2 * np.pi * carrier_freq * t)
            
            # Apply ring modulation
            modulated = audio * (1 + intensity * carrier)
            
            # Mix with original
            return (1 - intensity) * audio + intensity * modulated
            
        except Exception as e:
            logging.warning(f"Robotic resonance failed: {e}")
            return audio
    
    def _apply_distortion(self, audio: np.ndarray, amount: float) -> np.ndarray:
        """Apply subtle distortion for mechanical sound"""
        if amount == 0 or len(audio) == 0:
            return audio
        
        try:
            # Soft clipping distortion
            threshold = 1.0 - amount
            distorted = np.sign(audio) * (1 - np.exp(-np.abs(audio) / threshold))
            
            # Mix with original
            return (1 - amount) * audio + amount * distorted
            
        except Exception as e:
            logging.warning(f"Distortion failed: {e}")
            return audio
    
    def _add_echo(self, audio: np.ndarray, delay_ms: float, decay: float) -> np.ndarray:
        """Add echo effect"""
        if delay_ms == 0 or decay == 0 or len(audio) == 0:
            return audio
        
        try:
            # Calculate delay in samples
            delay_samples = int(delay_ms * self.sample_rate / 1000)
            
            if delay_samples >= len(audio) or delay_samples <= 0:
                return audio
            
            # Create echo
            echo_audio = np.zeros_like(audio)
            echo_audio[delay_samples:] = audio[:-delay_samples] * decay
            
            # Add echo to original
            return audio + echo_audio
            
        except Exception as e:
            logging.warning(f"Echo effect failed: {e}")
            return audio
    
    def create_custom_preset(self, 
                           pitch_shift: float = -2,
                           formant_shift: float = 0.85,
                           robotic_intensity: float = 0.3,
                           echo_delay_ms: float = 50,
                           echo_decay: float = 0.2,
                           distortion_amount: float = 0.1):
        """Create custom GLaDOS effect preset"""
        self.pitch_shift_semitones = pitch_shift
        self.formant_shift = formant_shift
        self.robotic_intensity = robotic_intensity
        self.echo_delay_ms = echo_delay_ms
        self.echo_decay = echo_decay
        self.distortion_amount = distortion_amount
        
        logging.info("Custom GLaDOS preset applied")
    
    def load_preset(self, preset_name: str):
        """Load predefined GLaDOS presets"""
        presets = {
            "subtle": {
                "pitch_shift": -1,
                "formant_shift": 0.9,
                "robotic_intensity": 0.2,
                "echo_delay_ms": 30,
                "echo_decay": 0.15,
                "distortion_amount": 0.05
            },
            "classic": {
                "pitch_shift": -2,
                "formant_shift": 0.85,
                "robotic_intensity": 0.3,
                "echo_delay_ms": 50,
                "echo_decay": 0.2,
                "distortion_amount": 0.1
            },
            "heavy": {
                "pitch_shift": -3,
                "formant_shift": 0.8,
                "robotic_intensity": 0.5,
                "echo_delay_ms": 70,
                "echo_decay": 0.3,
                "distortion_amount": 0.15
            }
        }
        
        if preset_name in presets:
            self.create_custom_preset(**presets[preset_name])
            logging.info(f"GLaDOS preset '{preset_name}' loaded")
        else:
            logging.warning(f"Preset '{preset_name}' not found")