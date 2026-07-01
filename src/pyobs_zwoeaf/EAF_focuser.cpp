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
		int device_id;

		EAF_WRAPPER() {
			this->device_id = 0;
		}

		bool connect(int device_number = 0) {
		    // in case someone gives a device_number smaller than 1 ...
			int eaf_count = EAFGetNum();
			if (eaf_count <= 0 || eaf_count < device_number) {
				return false;
			}

            // get ID of the chosen device!
            EAF_INFO eaf_info;
			if (EAFGetID(device_number, &eaf_info.ID) != EAF_SUCCESS) {
				return false;
			}
			EAFGetProperty(eaf_info.ID, &eaf_info);
			device_id = eaf_info.ID;

            // open camera
			return (EAFOpen(device_id) == EAF_SUCCESS);
		}

		int getMaximalStep() {
		    int max_steps;
			if (EAFGetMaxStep(device_id, &max_steps) == EAF_SUCCESS) {
				return max_steps;
            }
            return -1;
		}

		void setMaximalStep(int max_steps) {
			EAFSetMaxStep(device_id, max_steps);
		}

		bool getSound() {
		    bool sound;
			bool error = (EAFGetBeep(device_id, &sound) == EAF_SUCCESS);
            return error == EAF_SUCCESS && sound;
		}

		void setSound(bool sound) {
			EAFSetBeep(device_id, sound);
		}

		float getTemperature() {
		    float temperature;
			EAFGetTemp(device_id, &temperature);
			return temperature;
		}

		bool isMoving() {
    		bool moving, handcontrol;
			bool error = EAFIsMoving(device_id, &moving, &handcontrol);
            return error == EAF_SUCCESS && moving;
		}

		int getPosition() {
		    int position;
			if (EAFGetPosition(device_id, &position) == EAF_SUCCESS) {
				return position;
			}
            return -1;
		}

		void resetPosition(int ref_position) {
			EAFResetPostion(device_id, ref_position);
		}

		bool getDirection() {
		    bool direction;
			EAFGetReverse(device_id, &direction);
			return direction;
		}

		void setDirection(bool direction) {
			EAFSetReverse(device_id, direction);
		}

		int getStepRange() {
			if (isMoving()) {
				return -1;
			}

            int step_range;
			if (EAFStepRange(device_id, &step_range) == EAF_SUCCESS) {
				return step_range;
			} else {
				return -1;
			}
		}

		bool move(int target_position) {
			if (isMoving()) {
				return false;
			}

			int error = EAFMove(device_id, target_position);
			return (error == EAF_SUCCESS);
		}

		bool stop() {
			return (EAFStop(device_id) == EAF_SUCCESS);
		}

		int getBacklash() {
		    int backlash;
			EAFGetBacklash(device_id, &backlash);
			return backlash;
		}

		void setBacklash(int backlash) {
			EAFSetBacklash(device_id, backlash);
		}

		bool disconnect() {
			return (EAFClose(device_id) == EAF_SUCCESS);
		}
};

PYBIND11_MODULE(EAF_focuser, handle)
{
	handle.doc() = "This module is a c++ wrapper of the EAF motor driver for python3.";

	py::class_<EAF_WRAPPER>(handle, "EAF")
		.def(py::init<>())
		.def("connect", &EAF_WRAPPER::connect)
		.def("getMaximalStep", &EAF_WRAPPER::getMaximalStep)
		.def("setMaximalStep", &EAF_WRAPPER::setMaximalStep)
		.def("getSound", &EAF_WRAPPER::getSound)
		.def("setSound", &EAF_WRAPPER::setSound)
		.def("getTemperature", &EAF_WRAPPER::getTemperature)
		.def("isMoving", &EAF_WRAPPER::isMoving)
		.def("getPosition", &EAF_WRAPPER::getPosition)
		.def("resetPosition", &EAF_WRAPPER::resetPosition)
		.def("getDirection", &EAF_WRAPPER::getDirection)
		.def("setDirection", &EAF_WRAPPER::setDirection)
		.def("getStepRange", &EAF_WRAPPER::getStepRange)
		.def("move", &EAF_WRAPPER::move)
		.def("stop", &EAF_WRAPPER::stop)
		.def("getBacklash", &EAF_WRAPPER::getBacklash)
		.def("setBacklash", &EAF_WRAPPER::setBacklash)
		.def("disconnect", &EAF_WRAPPER::disconnect)
		;
}



