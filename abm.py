import argparse
from mesa import Agent
from mesa import Model
from mesa import DataCollector
from mesa.time import RandomActivation
import scipy.stats as ss
import numpy as np
import os
import json
from datetime import date, datetime
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

		self.leave_triage_queue_time = None
		self.leave_priority_queue_time = None
		self.discharge_time = None

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
			# patient_triage_copy = ctaskopy.deepcopy(self.patients_triaging)
			patient_to_pop = []
			for i in range(len(self.patients_triaging)):
				patient, entry_time = self.patients_triaging[i]

				if (self.model.current_tick - entry_time) >= patient.triage_time:

					if patient.ctask_status == 1:
						self.model.doctors.critical_patients.insert(0, patient)
						patient.triaged = True

					if (patient.ctask_status == 2) or (patient.ctask_status == 3):
						self.high_priority_queue.insert(0, patient)
						patient.triaged = True
					else:
						self.low_priority_queue.insert(0, patient)
						patient.triaged = True

					# patient_triage_copy.pop(i)
					patient_to_pop.append(i)
					self.n_busy -= 1
					patient.triaged = True

			for i in patient_to_pop:
				try:
					self.patients_triaging.pop(i)
				except:
					pass


			# self.patients_triaging = patient_triage_copy

		# Check if any nurse is free
		if self.n_busy < self.n_nurses and self.entry_queue:
			# Add someone to get triaged
			self.n_busy += 1
			patient = self.entry_queue.pop()
			patient.leave_triage_queue_time = self.model.current_tick
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
		self.n_critical = 0

	def get_patient(self):
		if self.critical_patients and self.n_critical < self.n_doctors:
			min_ctask = 10000
			backlog_patient = None

			# If a critical patient exists, remove the lowest priority patient right now
			# Keep track of their remaining ER time
			if self.current_patients:
				for i, patient, time in enumerate(self.current_patients):
					print(patient)
					if patient.ctask_status < min_ctask:
						backlog_patient = i
						min_ctask = patient.ctask_status

				backlog_patient, entry_time = self.current_patients.pop(backlog_patient)

				# This is the start time after the patients gets re-inputted
				remaining_time = self.model.current_tick - entry_time

				self.backlog.insert(0, (backlog_patient, remaining_time))
			critical_patient = self.critical_patients.pop()
			self.current_patients.append((critical_patient, self.model.current_tick))
			self.n_critical += 1

			if self.n_busy < self.n_doctors:
				self.n_busy += 1

		if self.model.triage_nurses.high_priority_queue and self.n_busy < self.n_doctors:
			patient = self.model.triage_nurses.high_priority_queue.pop()
			patient.leave_priority_queue_time = self.model.current_tick
			self.current_patients.append((patient, self.model.current_tick))
			self.n_busy += 1
			patient.seeing_doc = True

		if self.model.triage_nurses.low_priority_queue and self.n_busy < self.n_doctors:
			patient = self.model.triage_nurses.low_priority_queue.pop()
			patient.leave_priority_queue_time = self.model.current_tick
			self.current_patients.append((patient, self.model.current_tick))
			self.n_busy += 1
			patient.seeing_doc = True
		return

	def step(self):
		if self.n_busy < self.n_doctors:
			self.get_patient()

		if self.current_patients: 
			current_patients_copy = self.current_patients
			patients_to_pop = []
			for i in range(len(self.current_patients)):
				patient, entry_time = current_patients_copy[i]
				if (self.model.current_tick - entry_time) >= patient.er_service_time:
					if patient.ctask_status == 1:
						self.n_critical -= 1
					# current_patients_copy.pop(i)
					patients_to_pop.append(i)
					self.n_busy -= 1
					patient.discharged = True
					patient.discharge_time = self.model.current_tick
			for i in patients_to_pop:
				try:
					self.current_patients.pop(i)
				except:
					pass
			# self.current_patients = current_patients_copy
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

		self.datacollector = DataCollector(
			model_reporters = {
				'Patients Arrived': get_patients_arrived,
				'Patients Discharged': get_patients_discharged,
				'Patients Triaged': get_patients_triaged,
				'Patients Seeing Doc': get_patients_seeing_doc,
				'Triage Queue Size': get_triage_queue_size,
				'Low Priority Queue Size': get_low_priority_queue,
				'High Priority Queue Size': get_high_priority_queue,
				'Patients Triaging': get_patients_triaging,
				'Backlog': get_backlog,
				'Critical Patients': get_critical_patients,
				'Leave Triage Queue Time': get_leave_triage_queue_time,
				'Leave Priority Queue Time': get_leave_priority_queue_time,
				'Discharge Time': get_discharge_time
			}
		)

	def step(self):
		print("STEP")
		self.datacollector.collect(self)
		self.schedule.step()
		self.current_tick += 1

		return

def get_patients_arrived(model):
	patients_arrived = [patient.triage_queue for patient in model.patients]
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

def get_triage_queue_size(model):
	return len(model.triage_nurses.entry_queue)

def get_low_priority_queue(model):
	return len(model.triage_nurses.low_priority_queue)

def get_high_priority_queue(model):
	return len(model.triage_nurses.high_priority_queue)

def get_patients_triaging(model):
	return len(model.triage_nurses.patients_triaging)

def get_backlog(model):
	return len(model.doctors.backlog)

def get_critical_patients(model):
	return len(model.doctors.critical_patients)

def get_leave_triage_queue_time(model):
	patients = [np.nan if patient.leave_triage_queue_time is None else patient.leave_triage_queue_time for patient in model.patients]
	return np.nanmean(patients)

def get_leave_priority_queue_time(model):
	patients = [np.nan if patient.leave_priority_queue_time is None else patient.leave_priority_queue_time for patient in model.patients]
	return np.nanmean(patients)

def get_discharge_time(model):
	patients = [np.nan if patient.discharge_time is None else patient.discharge_time for patient in model.patients]
	return np.nanmean(patients)


def main(args):
	ctask_dist = [0.02, 0.25, 0.35, 0.28, 0.1]
	service_dist = [80, 45, 35, 20, 15]
	ticks = args.ticks
	er_model = ERModel(args.n_patients, args.n_triage_nurses, args.n_doctors, ticks, ctask_dist, service_dist)

	for i in range(ticks):
		er_model.step()

	run_stats = er_model.datacollector.get_model_vars_dataframe()
	print(run_stats)

	results_dir = os.path.join(os.path.abspath(os.getcwd()), 'results')

	if not os.path.exists(results_dir):
		os.mkdir(results_dir)

	run_dir = os.path.join(results_dir, datetime.now().strftime('%d-%m-%Y_%H_%M_%S'))
	os.mkdir(run_dir)


	with open(os.path.join(run_dir, 'params.txt'), 'w') as f:
		json.dump(args.__dict__, f, indent=2)

	return



if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'--n_patients',
		default = 5,
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
		default=20,
		type=int
		)
	args = parser.parse_args()

	main(args)




