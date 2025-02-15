#include <pybind11/pybind11.h>
#include "stdio.h"
#include "../lib/include/EAF_focuser.h"
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
		bool b_sound;

		// function variables
		int EAF_count; 			// number of found devices
		EAF_INFO EAFInfo; 		// EAF info structure
		int iSelectedID; 		// selected device id
		float f_temp; 			// temperature in fahrenheit?
		int pose; 		        // motor pose
		EAF_ERROR_CODE error; 	        // EAF error code error
		bool b_moving; 			// boolean if motor moving
		bool b_handcontrol; 	        // boolean if motor is moving by handcontrol -> does not exsist in our case ...
		int step_range;                 // The maximal range of steps
		bool capture; 			// capture useless returns

		EAF_WRAPPER(int device_number, int max_steps, int backlash, bool direction, bool b_sound)
		{
			this->device_number = device_number;
			this->max_steps = max_steps;
			this->backlash = backlash;
			this->direction = direction;
			this->b_sound = b_sound;
		}

		bool EAFConnect()
		{
			EAF_count = EAFGetNum();
			if(EAF_count <= 0 || EAF_count < device_number) // in case someone gives a device_number smaller than 1 ...
			{
				return false;
			}

			if(EAFGetID(device_number, &EAFInfo.ID) != EAF_SUCCESS) // get ID of the chosen device!
			{
				return false;
			}
			EAFGetProperty(EAFInfo.ID, &EAFInfo);
			iSelectedID = EAFInfo.ID;

			if(EAFOpen(iSelectedID) != EAF_SUCCESS)
			{
				return false; //printf("ERROR! Could not connect! Are you root?");
			} else {
				EAFSetMaximalStep();
				EAFSetterBacklash();
				EAFSetDirection();
				EAFSetSound();
				return true; //printf("Connected to EAF Focuser! Ready to use!")
			}
		}

		int EAFGetMaximalStep()
		{
			if(EAFGetMaxStep(iSelectedID, &max_steps) == EAF_SUCCESS)
			{
				return max_steps;
			} else {
				return -1;
			}

		}

		void EAFSetMaximalStep()
		{
			EAFSetMaxStep(iSelectedID, max_steps);
		}

		bool EAFGetSound()
		{
			if(EAFGetBeep(iSelectedID, &b_sound) == EAF_SUCCESS)
			{
				return b_sound;
			}
				return false;
		}

		void EAFSetSound()
		{
			EAFSetBeep(iSelectedID, b_sound);
		}

		float EAFTemperature()
		{
			EAFGetTemp(iSelectedID, &f_temp);
			return f_temp;
		}

		bool EAFProperty()
		{
			error = EAFGetProperty(iSelectedID, &EAFInfo);
			if(error == EAF_SUCCESS)
			{
				return true;
			} else {
				return false;
			}
		}

		bool EAFMoving()
		{
			error = EAFIsMoving(iSelectedID, &b_moving, &b_handcontrol);
			if(error == EAF_SUCCESS)
			{
				if(b_moving == true)
				{
					return true;
				} else {
					return false;
				}
			} else {
				return false;
			}
		}

		int EAFGetPose()
		{
			if(EAFGetPosition(iSelectedID, &pose) == EAF_SUCCESS)
			{
				return pose;
			} else {
				return -1;
			}
		}

		void EAFSetPose(int ref_pose)
		{
			EAFResetPostion(iSelectedID, ref_pose);
			pose = ref_pose;
		}

		bool EAFGetDirection()
		{
			EAFGetReverse(iSelectedID, &direction);
			return direction;
		}

		void EAFSetDirection()
		{
			EAFSetReverse(iSelectedID, direction);
		}

		int EAFMoveRange()
		{
			capture = EAFMoving();
			if(b_moving == true)
			{
				return -1;
			}

			if(EAFStepRange(iSelectedID, &step_range) == EAF_SUCCESS)
			{
				return step_range;
			} else {
				return -1;
			}
		}

		bool EAFMoveToPose(int target_pose) {

			capture = EAFMoving();
			if(b_moving == true)
			{
				return false;
			}

			error = EAFMove(iSelectedID, target_pose);
			if(error == EAF_SUCCESS) {
				b_moving = true;
				return true;
			}
				return false;
		}

		bool EAFMoveStop() {
			if(EAFStop(iSelectedID) == EAF_SUCCESS)
			{
			        return true;
			} else {
			        return false;
			}
		}

		int EAFGetterBacklash()
		{
			EAFGetBacklash(iSelectedID, &backlash);
			return backlash;

		}

		void EAFSetterBacklash()
		{
			EAFSetBacklash(iSelectedID, backlash);
		}

		bool EAFDisconnect()
		{
			if(EAFClose(iSelectedID) == EAF_SUCCESS)
			{
			        return true;
			} else {
			        return false;
			}
		}
};

PYBIND11_MODULE(pybind_wrapper, handle)
{
	handle.doc() = "This module is a c++ wrapper of the EAF motor driver for python3.";

	py::class_<EAF_WRAPPER>(handle, "EAF")
		.def(py::init<int, int, int, bool, bool>())
		.def("Connect", &EAF_WRAPPER::EAFConnect)
		.def("GetMaximalStep", &EAF_WRAPPER::EAFGetMaximalStep)
		.def("SetMaximalStep", &EAF_WRAPPER::EAFSetMaximalStep)
		.def("GetSound", &EAF_WRAPPER::EAFGetSound)
		.def("SetSound", &EAF_WRAPPER::EAFSetSound)
		.def("Temperature", &EAF_WRAPPER::EAFTemperature)
		.def("Property", &EAF_WRAPPER::EAFProperty)
		.def("Moving", &EAF_WRAPPER::EAFMoving)
		.def("GetPose", &EAF_WRAPPER::EAFGetPose)
		.def("SetPose", &EAF_WRAPPER::EAFSetPose)
		.def("GetDirection", &EAF_WRAPPER::EAFGetDirection)
		.def("SetDirection", &EAF_WRAPPER::EAFSetDirection)
		.def("MoveRange", &EAF_WRAPPER::EAFMoveRange)
		.def("MoveToPose", &EAF_WRAPPER::EAFMoveToPose)
		.def("MoveStop", &EAF_WRAPPER::EAFMoveStop)
		.def("GetBacklash", &EAF_WRAPPER::EAFGetterBacklash)
		.def("SetBacklash", &EAF_WRAPPER::EAFSetterBacklash)
		.def("Disconnect", &EAF_WRAPPER::EAFDisconnect)
		;
}



