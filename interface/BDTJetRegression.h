#ifndef bdtjetregression_h
#define bdtjetregression_h

// Standard libraries
#include <vector>
#include <string>
#include <cmath>
#include <iostream>

#include <xgboost/c_api.h>


class BDTJetRegression {
    public:
        BDTJetRegression();
        BDTJetRegression(std::string filename, bool use_sigmoid);
        ~BDTJetRegression();
        float get_regressed_pt(std::vector<float> inputs);

    private:
        BoosterHandle booster_;
        bool use_sigmoid_;
        float sigmoid(float x) const;
};

#endif