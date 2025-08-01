#include <pybind11/pybind11.h>
#include "stdio.h"
#include "EAF_focuser.h"
#include <sys/time.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <signal.h>

// python3 needs pybind11 package for installation
// compile with c++ -O3 -Wall -shared -std=c++11 -fPIC $(python3 -m pybind11 --includes) eaf_pybind_wrapper.cpp -o eaf_pybind_module$(python3-config --extension-suffix) -m64 -lrt -ludev ../lib/x64/libEAFFocuser.a -I ../include -m64 -lrt -ludev -lpthread
namespace py = pybind11;

class EAF_WRAPPER
{
	public:
		// constructor variables
		int device_number;
		int max_steps;
		int backlash;
		bool direction;
		bool sound;

		// function variables
		int eaf_count; 			// number of found devices
		EAF_INFO eaf_info; 		// EAF info structure
		int selected_id; 		// selected device id
		float temperature; 	    // temperature in fahrenheit?
		int position; 		    // motor position
		EAF_ERROR_CODE error; 	// EAF error code error
		bool moving; 			// boolean if motor moving
		bool handcontrol; 	    // boolean if motor is moving by handcontrol -> does not exsist in our case ...
		int step_range;         // The maximal range of steps
		bool capture; 			// capture useless returns

		EAF_WRAPPER(int device_number, int max_steps, int backlash, bool direction, bool sound) {
			this->device_number = device_number;
			this->max_steps = max_steps;
			this->backlash = backlash;
			this->direction = direction;
			this->sound = sound;
		}

		bool Connect() {
		    // in case someone gives a device_number smaller than 1 ...
			eaf_count = EAFGetNum();
			if (eaf_count <= 0 || eaf_count < device_number) {
				return false;
			}

            // get ID of the chosen device!
			if (EAFGetID(device_number, &eaf_info.ID) != EAF_SUCCESS) {
				return false;
			}
			EAFGetProperty(eaf_info.ID, &eaf_info);
			selected_id = eaf_info.ID;

			if(EAFOpen(selected_id) != EAF_SUCCESS) {
				return false; //printf("ERROR! Could not connect! Are you root?");
			} else {
				SetMaximalStep();
				SetBacklash();
				SetDirection();
				SetSound();
				return true; //printf("Connected to EAF Focuser! Ready to use!")
			}
		}

		int GetMaximalStep() {
			if (EAFGetMaxStep(selected_id, &max_steps) == EAF_SUCCESS) {
				return max_steps;
			} else {
				return -1;
			}

		}

		void SetMaximalStep() {
			EAFSetMaxStep(selected_id, max_steps);
		}

		bool GetSound() {
			if (EAFGetBeep(selected_id, &sound) == EAF_SUCCESS) {
				return sound;
			}
            return false;
		}

		void SetSound() {
			EAFSetBeep(selected_id, sound);
		}

		float Temperature() {
			EAFGetTemp(selected_id, &temperature);
			return temperature;
		}

		bool Property() {
			error = EAFGetProperty(selected_id, &eaf_info);
			return (error == EAF_SUCCESS);
		}

		bool Moving() {
			error = EAFIsMoving(selected_id, &moving, &handcontrol);
            return error == EAF_SUCCESS && moving;
		}

		int GetPosition() {
			if (EAFGetPosition(selected_id, &position) == EAF_SUCCESS) {
				return position;
			} else {
				return -1;
			}
		}

		void SetPosition(int ref_position) {
			EAFResetPostion(selected_id, ref_position);
			position = ref_position;
		}

		bool GetDirection() {
			EAFGetReverse(selected_id, &direction);
			return direction;
		}

		void SetDirection() {
			EAFSetReverse(selected_id, direction);
		}

		int MoveRange() {
			capture = Moving();
			if (moving) {
				return -1;
			}

			if (EAFStepRange(selected_id, &step_range) == EAF_SUCCESS) {
				return step_range;
			} else {
				return -1;
			}
		}

		bool MoveToPosition(int target_position) {
			capture = Moving();
			if (moving) {
				return false;
			}

			error = EAFMove(selected_id, target_position);
			if(error == EAF_SUCCESS) {
				moving = true;
				return true;
			}
            return false;
		}

		bool MoveStop() {
			return (EAFStop(selected_id) == EAF_SUCCESS);
		}

		int GetterBacklash() {
			EAFGetBacklash(selected_id, &backlash);
			return backlash;
		}

		void SetBacklash() {
			EAFSetBacklash(selected_id, backlash);
		}

		bool Disconnect() {
			return (EAFClose(selected_id) == EAF_SUCCESS);
		}
};

PYBIND11_MODULE(pybind_wrapper, handle)
{
	handle.doc() = "This module is a c++ wrapper of the EAF motor driver for python3.";

	py::class_<EAF_WRAPPER>(handle, "EAF")
		.def(py::init<int, int, int, bool, bool>())
		.def("Connect", &EAF_WRAPPER::Connect)
		.def("GetMaximalStep", &EAF_WRAPPER::GetMaximalStep)
		.def("SetMaximalStep", &EAF_WRAPPER::SetMaximalStep)
		.def("GetSound", &EAF_WRAPPER::GetSound)
		.def("SetSound", &EAF_WRAPPER::SetSound)
		.def("Temperature", &EAF_WRAPPER::Temperature)
		.def("Property", &EAF_WRAPPER::Property)
		.def("Moving", &EAF_WRAPPER::Moving)
		.def("GetPosition", &EAF_WRAPPER::GetPosition)
		.def("SetPosition", &EAF_WRAPPER::SetPosition)
		.def("GetDirection", &EAF_WRAPPER::GetDirection)
		.def("SetDirection", &EAF_WRAPPER::SetDirection)
		.def("MoveRange", &EAF_WRAPPER::MoveRange)
		.def("MoveToPosition", &EAF_WRAPPER::MoveToPosition)
		.def("MoveStop", &EAF_WRAPPER::MoveStop)
		.def("GetBacklash", &EAF_WRAPPER::GetterBacklash)
		.def("SetBacklash", &EAF_WRAPPER::SetBacklash)
		.def("Disconnect", &EAF_WRAPPER::Disconnect)
		;
}



