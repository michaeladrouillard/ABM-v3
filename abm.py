import argparse
from mesa import Agent
from mesa import Model 
from mesa.time import RandomActivation
import scipy.stats as ss
import numpy as np

# ctask 1 - immediate
# ctask 2 - 15 minutes
# ctask 3 - 45 min
# ctask 4 - 60 min
# ctask 5 - 120 min


class Patient(Agent):
	def __init__(self, unique_id, model, ctask_dist, service_distribution):
		super().__init__(unique_id, model)
		self.unique_id = unique_id
		self.ctask_status = np.random.choice(5, 1, ctask_dist)
		self.er_service_time = ss.poisson(service_distribution[int(self.ctask_status - 1)]).rvs()
		self.triage_entry_time = np.int(ss.beta(3, 3).rvs() * self.model.ticks) + 1
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
		print("PATIENT{} WORKING".format(self.unique_id))
		if not self.triaged and (self.model.current_tick >= self.triage_entry_time):
			self.triage_queue = True

		return


class TriageNurses(Agent):
	def __init__(self, unique_id, model, n_nurses):
		super().__init__(unique_id, model)
		self.entry_queue = []
		self.n_nurses = n_nurses
		self.n_busy = 0
		self.patients_triaging = []

		# ctask 2 and ctask 3
		self.high_priority_queue = []

		# ctask 4 and ctask 5
		self.low_prioity_queue = []

	def step(self):
		# Enter new patients into the triage entry queue
		for patient in self.model.patients:
			if patient.triage_queue:
				self.entry_queue.insert(0)

		# Release patients from nurses if time is up
		for i in range(self.n_nurses):
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

class Doctors(Agent):
	def __init__(self, unique_id, model, n_doctors):
		super().__init__(unique_id, model)
		self.n_doctors = n_doctors
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
		for i in range(self.n_doctors):
			patient, entry_time = self.current_patients[i]
			if (self.model.current_tick - entry_time) >= patient.service_time:
				self.current_patients.pop(i)
				self.n_busy -= 1
				patient.discharged = True

		if self.n_busy < self.n_doctors:
			self.get_patient()

		return

class ERModel(Model):
	def __init__(self, n_patients, n_triage_nurses, n_doctors, ticks, ctask_dist, service_dist):
		self.ticks = ticks
		self.current_tick = 1
		self.n_patients = n_patients
		self.n_triage_nurses = n_triage_nurses
		self.n_doctors = n_doctors
		self.ctask_dist = ctask_dist
		self.service_dist = service_dist


		self.schedule = RandomActivation(self)
		self.patients = []
		for i in range(self.n_patients):
			patient = Patient(i, self, self.ctask_dist, self.service_dist)
			self.schedule.add(patient)

			self.patients.append(patient)

		self.triage_nurses = TriageNurses(self.n_patients + 1, self, self.n_triage_nurses)
		self.schedule.add(self.triage_nurses)

		self.doctors = Doctors(self.n_patients + 2, self, self.n_doctors)
		self.schedule.add(self.doctors)

	def step(self):
		print("STEP")
		self.schedule.step()
		self.current_tick += 1

		return

def main(args):
	ctask_dist = [0.02, 0.25, 0.35, 0.28, 0.1]
	service_dist = [80, 45, 35, 20, 15]
	ticks = args.ticks
	er_model = ERModel(args.n_patients, args.n_triage_nurses, args.n_doctors, ticks, ctask_dist, service_dist)

	for i in range(ticks):
		er_model.step()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'--n_patients',
		default = 200,
		type = int)

	parser.add_argument(
		'--n_triage_nurses',
		default = 3,
		type = int
		)

	parser.add_argument(
		'--n_doctors',
		default = 2,
		type = int
		)
	parser.add_argument(
		'--ticks',
		default=500,
		type=int
		)
	args = parser.parse_args()

	main(args)




