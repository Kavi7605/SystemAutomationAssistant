from unittest.mock import MagicMock
from unittest.mock import patch

class TestVoiceIntegration:
    @patch("src.voice.voice_listener.VoiceListener")
    @patch("builtins.input")
    def test_voice_confirmation_flow_yes(self, mock_input, mock_listener_class):
        mock_listener = MagicMock()
        mock_listener_class.return_value = mock_listener
        mock_listener.listen.return_value = {"transcript": "open github", "model": "medium.en", "device": "CPU", "duration": 1.2}
        
        # Sequence of inputs: 1. mode=V, 2. proceed=Y, 3. mode=Q
        mock_input.side_effect = ["V", "Y", "Q"]
        
        self.engine.executor.execute.return_value = {"status": "success", "message": "Done"}
        
        self.engine.start()
        
        call_kwargs = self.engine.history_manager.add_entry.call_args[1]
        assert call_kwargs.get("source") == "voice"
        assert call_kwargs.get("user_command") == "open github"

    @patch("src.voice.voice_listener.VoiceListener")
    @patch("builtins.input")
    def test_voice_confirmation_flow_no(self, mock_input, mock_listener_class):
        mock_listener = MagicMock()
        mock_listener_class.return_value = mock_listener
        mock_listener.listen.return_value = {"transcript": "open badwebsite", "model": "medium.en"}
        
        # Sequence of inputs: 1. mode=V, 2. proceed=N, 3. mode=Q
        mock_input.side_effect = ["V", "N", "Q"]
        
        # Reset any calls that happened during init
        self.engine.history_manager.add_entry.reset_mock()
        self.engine.start()
        
        # Should not have called add_entry because it was cancelled
        self.engine.history_manager.add_entry.assert_not_called()
