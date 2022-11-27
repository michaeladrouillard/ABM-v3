import argparse
from mesa import Agent
from mesa import Model 
from mesa.time import RandomActivation
import scipy.stats as ss
import numpy as np
import copy

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
		self.low_priority_queue = []

	def step(self):
		# Enter new patients into the triage entry queue
		for patient in self.model.patients:
			if patient.triage_queue:
				self.entry_queue.insert(0, patient)

		# Release patients from nurses if time is up
		if self.patients_triaging:
			patient_triage_copy = copy.deepcopy(self.patients_triaging)
			for i in range(len(self.patients_triaging)):
				patient, entry_time = self.patients_triaging[i]

				if (self.model.current_tick - entry_time) >= patient.triage_time:

					if (patients.ctask_status == 1):
						self.model.doctors.critical_patients.insert(0, patient)
						patient_triaged = True

					if (patient.ctask_status == 2) or (patient.ctask_status == 3):
						self.high_priority_queue.insert(0, patient)
						patient.triaged = True
					else:
						self.low_priority_queue.insert(0, patient)
						patient.triaged = True

					patient_triage_copy.pop(i)
					self.n_busy -= 1
					patient.triaged = True

			self.patients_triaging = patient_triage_copy

		# Check if any nurse is free
		if self.n_busy < self.n_nurses and self.entry_queue:
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
		self.critical_patients = []

	def get_patient(self):
		if self.critical_patients:
			for patient in self.current_patients:
		if self.model.triage_nurses.high_priority_queue and self.n_busy < self.n_doctors:
			patient = self.model.triage_nurses.high_priority_queue.pop()
			self.current_patients.append((patient, self.model.current_tick))
			self.n_busy += 1
			patient.seeing_doc = True

		if self.model.triage_nurses.low_priority_queue and self.n_busy < self.n_doctors:
			patient = self.model.triage_nurses.low_priority_queue.pop()
			self.current_patients.append((patient, self.model.current_tick))
			self.n_busy += 1
			patient.seeing_doc = True
		return

	def step(self):
		if self.n_busy < self.n_doctors:
			self.get_patient()


		if self.current_patients: 
			current_patients_copy = self.current_patients
			for i in range(len(self.current_patients)):
				patient, entry_time = current_patients_copy[i]
				if (self.model.current_tick - entry_time) >= patient.er_service_time:
					current_patients_copy.pop(i)
					self.n_busy -= 1
					patient.discharged = True
			self.current_patients = current_patients_copy
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

def get_patients_arrived(model):
	patients_arrived = [patient._triage_queue for patient in model.patients]
	return np.sum(patients_arrived)

def get_patients_discharged(model):
	patients_discharged = [patient.discharged for patient in model.patients]
	return np.sum(patients_discharged)

def get_patients_triaged(model):
	patients_triaged = [patient.triaged for patient in model.patients]
	return np.sum(patients_triaged)

def get_patients_seeing_doc(model):
	patients_seeing_doc = [patient.seeing_doc for patient in model.patients]
	return np.sum(patients_seeing_doc)

def main(args):
	ctask_dist = [0.02, 0.25, 0.35, 0.28, 0.1]
	service_dist = [80 * 60, 45 * 60, 35 * 60, 20 * 60, 15 * 60]
	ticks = args.ticks
	er_model = ERModel(args.n_patients, args.n_triage_nurses, args.n_doctors, ticks, ctask_dist, service_dist)

	for i in range(ticks):
		er_model.step()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'--n_patients',
		default = 50,
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
		default=3600,
		type=int
		)
	args = parser.parse_args()

	main(args)




