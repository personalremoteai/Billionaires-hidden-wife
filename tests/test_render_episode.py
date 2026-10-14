import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import render_episode

class RenderInputTests(unittest.TestCase):
    def test_valid_episode_shape(self):
        data = {'episode_number': 1, 'scenes': [{'scene_number': 1, 'duration_seconds': 8, 'dialogue': []}]}
        self.assertEqual(render_episode.validate_episode(data, 1), [])

    def test_wrong_episode_number_rejected(self):
        self.assertTrue(render_episode.validate_episode({'episode_number': 2, 'scenes': [{}]}, 1))

    def test_dialogue_object_shape(self):
        lines = render_episode.dialogue_lines({'dialogue': [{'speaker': 'Isabella Hart', 'line': 'I came back.'}]})
        self.assertEqual(lines[0]['speaker'], 'Isabella Hart')
        self.assertEqual(lines[0]['line'], 'I came back.')

    def test_plain_text_dialogue_supported(self):
        lines = render_episode.dialogue_lines({'dialogue': ['Hello there.']})
        self.assertEqual(lines[0]['line'], 'Hello there.')

    def test_voice_defaults_are_stable(self):
        self.assertEqual(render_episode.voice_for('Isabella Hart'), 'en-US-JennyNeural')
        self.assertEqual(render_episode.voice_for('Alexander Sterling'), 'en-US-GuyNeural')

if __name__ == '__main__':
    unittest.main()
