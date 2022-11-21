from mesa import Agent
import scipy.stats as ss

# ctask 1 - immediate
# ctask 2 - 15 minutes
# ctask 3 - 45 min
# ctask 4 - 60 min
# ctask 5 - 120 min


class Patient(Agent):
	def __init__(self, unique_id, model, ctask_dist, service_distribution):
		super().__init__(unique_id, model, ctask_dist, service_distribution)
		self.ctask_status = np.random.choice(5, 1, ctask_dist)
		self.er_service_time = ss.poisson(service_distribution[self.ctask_status]).rvs()
		self.triage_entry_time = np.int(ss.beta(3, 3).rvs() * ticks) + 1
		self.triage_time = ss.poisson(3).rvs() + 1

		self.triage_queue = False
		self.triaged = False
		self.seeing_doc = False
		self.discharged = False

	def get_triaged(self):
		self.triaged = True
		return

	def get_discharged(self):
		self.discharged = True
		return

	def step(self):
		if not self.triage and (self.model.current_tick >= self.triage_entry_time):
			self.triage_queue = True

		return


class TriageNurses(Agent):
	def __init__(self, unique_id, model, n_nurses, patients):
		super().__init__(unique_id, model, n_nurses)
		self.entry_queue = []
		self.n_busy = 0
		self.patients_triaging = []

		# ctask 2 and ctask 3
		self.high_priority_queue = []

		# ctask 4 and ctask 5
		self.low_prioity_queue = []

	def step(self):
		# Enter new patients into the triage entry queue
		for patient in patients:
			if patient.triage_queue:
				self.entry_queue.insert(0)

		# Release patients from nurses if time is up
		for i in range(n_nurses):
			patient, entry_time = self.patients_triaging[i]
			if (self.model.current_tick - entry_time) >= patient.triage_time:

				if (patient.ctask_status == 2) or (patient.ctask_status == 3):
					self.high_priority.queue.insert(0)
				else:
					self.low_priority.queue.insert(0)

				self.patients_triaging.pop(i)
				self.n_busy -= 1
				patient.triaged = True

		# Check if any nurse is free
		if n_busy < n_nurses:
			# Add someone to get triaged
			self.n_busy += 1
			patient = self.entry_queue.pop()
			self.patients_triaging.append((patient, self.model.current_tick))
		return

	class Doctor(Agent):
		def __init__(self, unique_id, model, n_doctors):
			super().__init__(unique_id, model, n_doctors)
			self.backlog = []
			self.n_busy = 0
			self.current_patients = []

		def get_patient(self):
			if self.model.triage_nurses.high_priority and self.n_busy < self.n_doctors:
				patient = self.model.triage_nurses.high_priority.pop()
				self.current_patients.append((patient, self.model.current_tick))
				self.n_busy += 1
				patient.seeing_doc = True

			if not self.model.triage_nurses.high_priority and self.n_busy < self.n_doctors:
				patient = self.triage_nurses.low_priority.pop()
				self.current_patients.append((patient, self.model.current_tick))
				self.n_busy += 1
				patient.seeing_doc = True
			return

		def step(self):
			for i in range(n_doctors):
				patient, entry_time = self.current_patients[i]
				if (self.model.current_tick - entry_time) >= patient.service_time:
					self.current_patients.pop(i)
					self.n_busy -= 1
					patient.discharged = True

			if self.n_busy < self.n_doctors:
				self.get_patient()

			return

