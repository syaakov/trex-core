/*
 Itay Marom
 Hanoch Haim
 Cisco Systems, Inc.
*/

/*
Copyright (c) 2015-2016 Cisco Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
#ifndef __TREX_STL_MESSAGING_H__
#define __TREX_STL_MESSAGING_H__

#include "trex_messaging.h"
#include "trex_defs.h"

class CSyncBarrier;


// create tcp batch per DP core
class TrexAstfDpCreateTcp : public TrexCpToDpMsgBase {
public:
    TrexAstfDpCreateTcp();
    virtual TrexCpToDpMsgBase* clone(void);
    virtual bool handle(TrexDpCore *dp_core);
};

// delete tcp batch per DP core
class TrexAstfDpDeleteTcp : public TrexCpToDpMsgBase {
public:
    TrexAstfDpDeleteTcp();
    virtual TrexCpToDpMsgBase* clone(void);
    virtual bool handle(TrexDpCore *dp_core);
};

/**
 * a message to start traffic
 *
 */
class TrexAstfDpStart : public TrexCpToDpMsgBase {
public:
    TrexAstfDpStart(double duration);
    virtual TrexCpToDpMsgBase* clone(void);
    virtual bool handle(TrexDpCore *dp_core);
private:
    double m_duration;
};

/**
 * a message to stop traffic
 *
 */
class TrexAstfDpStop : public TrexCpToDpMsgBase {
public:
    TrexAstfDpStop();
    virtual TrexCpToDpMsgBase* clone(void);
    virtual bool handle(TrexDpCore *dp_core);
};





#endif /* __TREX_STL_MESSAGING_H__ */

