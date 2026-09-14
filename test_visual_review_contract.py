import json
import pytest
from image_consistency import _result, ImageConsistencyError
from scene_errors import CHECK_IDS

EXPECTED={'expression':'markedly uncomfortable','skin_color':'mild pallor','mottling':False,
          'diaphoresis':'mild','mental_status':'drowsy','work_of_breathing':'increased','respiratory_support':'none'}

def report():
    return {'checks':{k:True for k in CHECK_IDS},'uncertain_checks':[], 'conflict_evidence':[],
            'observations':{'devices':['blood_pressure_cuff','pulse_oximeter','ecg_electrodes'],
                            'unexpected_findings':[], 'skin':'natural_or_subtle_pallor'}}

def test_reported_screenshot_monitoring_is_not_treatment_and_mild_pallor_is_labelled():
    r=report()
    for check, finding in [('skin_color','Natural warm tones, not notably desaturated.'),
                           ('respiratory_support','Pulse oximeter and cuff are attached.'),
                           ('no_unrequested_signs','Connected monitoring and ECG wires.')]:
        r['checks'][check]=False
        r['conflict_evidence'].append({'check':check,'finding':finding})
    result=_result(json.dumps(r),EXPECTED)
    assert result['accepted'] and all(result['checks'].values())
    assert result['limitations']==['mild_skin_color']

@pytest.mark.parametrize('device',['nasal_cannula','simple_mask','niv_mask','endotracheal_tube'])
def test_real_unrequested_respiratory_interface_still_rejects(device):
    r=report();r['observations']['devices'].append(device)
    with pytest.raises(ImageConsistencyError) as e:_result(json.dumps(r),EXPECTED)
    assert 'respiratory_support' in e.value.failed_checks

def test_missing_required_oxygen_rejects_even_with_connected_monitors():
    with pytest.raises(ImageConsistencyError) as e:
        _result(json.dumps(report()),{**EXPECTED,'respiratory_support':'nasal cannula'})
    assert 'respiratory_support' in e.value.failed_checks

@pytest.mark.parametrize('finding',['bleeding','injury','cyanosis','unrequested_active_treatment'])
def test_real_unrequested_findings_still_reject(finding):
    r=report();r['observations']['unexpected_findings']=[finding]
    with pytest.raises(ImageConsistencyError) as e:_result(json.dumps(r),EXPECTED)
    assert 'no_unrequested_signs' in e.value.failed_checks

@pytest.mark.parametrize('skin',['marked_flushing','cyanosis'])
def test_visible_skin_conflict_is_not_excused_as_mild_pallor(skin):
    r=report();r['observations']['skin']=skin
    with pytest.raises(ImageConsistencyError) as e:_result(json.dumps(r),EXPECTED)
    assert 'skin_color' in e.value.failed_checks

def test_unclear_required_interface_is_not_silently_accepted():
    r=report();r['uncertain_checks']=['respiratory_support']
    with pytest.raises(ImageConsistencyError):_result(json.dumps(r),EXPECTED)

def test_unknown_observed_device_is_not_silently_ignored():
    r=report();r['observations']['devices']=['unknown_device']
    with pytest.raises(ImageConsistencyError) as e:_result(json.dumps(r),EXPECTED)
    assert e.value.reason_code=='invalid_response'

def test_photographic_limitation_reaches_visible_scene():
    from scene_pipeline import ScreenedImage
    from clinical_scene import scene_html
    assert 'Mild pallor: not discernible' in scene_html(ScreenedImage('abc',['mild_skin_color']),'monitor')


def test_rechecking_candidate_does_not_generate_another_image(monkeypatch):
    import scene_pipeline
    seen=[]
    monkeypatch.setattr(scene_pipeline,'_screen',lambda candidate,*args,**kw: seen.append(candidate) or 'approved')
    assert scene_pipeline.screened_existing_scene('existing-pixels',{},'key','model')=='approved'
    assert seen==['existing-pixels']


def test_retained_candidate_job_skips_initial_generation(monkeypatch):
    from concurrent.futures import Future
    import scene_jobs
    class Pool:
        def submit(self, function, *args):
            f=Future();f.set_result(function(*args));return f
    monkeypatch.setattr(scene_jobs,'_POOL',Pool())
    jobs=scene_jobs.SceneJobs()
    jobs.review_candidate=lambda *args:'reviewed-existing-image'
    def unexpected_generation(*args):raise AssertionError('Unnecessary image generation')
    jobs.request('same-appearance',{},'key','model',unexpected_generation,unexpected_generation)
    assert jobs.current('same-appearance')=='reviewed-existing-image'
    assert jobs.review_candidate is None
