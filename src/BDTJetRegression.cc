#include "L1DS/Modules/interface/BDTJetRegression.h"

float BDTJetRegression::sigmoid(float x) const {
    return (1. / (1 + std::exp(-1. * x)));
}

BDTJetRegression::BDTJetRegression(std::string filename, bool use_sigmoid) {
    XGBoosterCreate(NULL, 0, &booster_);
    XGBoosterLoadModel(booster_, filename.c_str());
    use_sigmoid_ = use_sigmoid;
}

// Destructor
BDTJetRegression::~BDTJetRegression() {}

float BDTJetRegression::get_regressed_pt(std::vector<float> inputs){
    float result = -9999.;
    float values[1][inputs.size()];
    int ivar = 0;

    for (auto& var : inputs) {
        values[0][ivar] = var;
        ++ivar;
    }
    
    DMatrixHandle dvalues;
    XGDMatrixCreateFromMat(reinterpret_cast<float*>(values), 1, inputs.size(), -9999., &dvalues);

    bst_ulong out_dim;
    float const* out_result = NULL;

    auto ret = XGBoosterPredict(
        booster_, dvalues, 0, 0, 0, &out_dim, &out_result);

    XGDMatrixFree(dvalues);

    if(ret == 0){
        result = out_result[0];
    }

    if (use_sigmoid_) {
        result = sigmoid(result);
    }

    //std::cout << "Regressed pt: " << result << std::endl;
    return result;
}
