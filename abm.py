from mesa import Agent
import scipy.stats as ss

# ctask 1 - immediate
# ctask 2 - 15 minutes
# ctask 3 - 45 min
# ctask 4 - 60 min
# ctask 5 - 120 min

global CTASK_DIST 

class Patient(Agent):
	def __init__(self, unique_id, model, ctask_dist, service_distribution):
		super().__init__(unique_id, model, ctask_dist, service_distribution)
		self.ctask_status = np.random.choice(5, 1, ctask_dist)
		self.service_time = ss.poisson(service_distribution[self.ctask_status]).rvs()
		self.start_time = np.int(ss.beta(3, 3).rvs() * ticks) + 1
		self.service_start_time = None
		self.discharged_time = None

		self.triaged = False
		self.seeing_doc = False
		self.discharged = False

	def get_triaged(self):
		self.triaged = True
		return

	def get_discharged(self):
		self.discharged = True
		return 

class TriageQueue(Agent):
	def __init__(self, unique_id, model):
		super().__init__(unique_id, model)
		self.queue = []
		self.patients = 0

	def triage_new(self, patient):
		if patient.ctask_status == 1:
			self.queue.append(patient)
		else:
			self.queue.insert(0, patient)
		return




