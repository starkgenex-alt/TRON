import tron
from live_simulation import design_ai_accelerator, simulate_thermal, estimate_manufacturing_cost, validate_training_pipeline

tron.set_config_url('http://127.0.0.1:9000')

print('using server', tron.get_config().url)

design_future = design_ai_accelerator(512, 75)
print('design_future', design_future)
design = design_future.get()
print('design', design)

thermal_future = simulate_thermal(design)
print('thermal_future', thermal_future)
try:
    thermal = thermal_future.get()
    print('thermal', thermal)
except Exception as e:
    print('thermal get exception', repr(e))

cost_future = estimate_manufacturing_cost(design)
print('cost_future', cost_future)
try:
    cost = cost_future.get()
    print('cost', cost)
except Exception as e:
    print('cost get exception', repr(e))

validation_future = validate_training_pipeline(design, dataset_size_tb=4.5)
print('validation_future', validation_future)
try:
    validation = validation_future.get()
    print('validation', validation)
except Exception as e:
    print('validation get exception', repr(e))
