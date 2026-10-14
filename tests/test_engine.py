import importlib.util, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('engine',ROOT/'tools'/'production_engine.py')
engine=importlib.util.module_from_spec(spec); spec.loader.exec_module(engine)
class ValidationTests(unittest.TestCase):
    def test_rejects_non_object(self): self.assertTrue(engine.validate([]))
    def test_requires_scenes(self): self.assertTrue(any('scenes' in e for e in engine.validate({'episode_number':1},1)))
    def test_valid_shape(self):
        o={'episode_number':1,'title':'T','logline':'L','previously_established':[],'scenes':[{'location':'A','time':'Night','visual_action':'Action','dialogue':[],'image_prompt':'Vertical image prompt'} for _ in range(3)],'cliffhanger':'A specific reveal happens.'}
        self.assertEqual(engine.validate(o,1),[])
if __name__=='__main__': unittest.main()
