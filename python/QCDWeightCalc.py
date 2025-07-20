# Calculates xs weights from a given json for QCD samples
import os

from analysis_tools.utils import import_root, randomize
from Base.Modules.baseModules import JetLepMetSyst

ROOT = import_root()

class QCDWeightProducer(JetLepMetSyst):
    def __init__(self, *args, **kwargs):
        default_name = "qcd_weight"

        #default_json_path = os.path.expandvars("$CMSSW_BASE/src/L1DS/Modules/data/qcd_with_weights.json")
        default_json_path = os.path.expandvars("$CMSSW_BASE/src/L1DS/Modules/data/qcd_with_weights_2025.json")

        self.json_path = kwargs.pop("json_path", default_json_path)
        self.json = self.json_path.replace("/", "_").replace(".", "_")
        self.weight_name = kwargs.pop("weight_name", default_name)

        super(QCDWeightProducer, self).__init__(*args, **kwargs)

        base = "{}/{}/src/L1DS/Modules".format(
            os.getenv("CMT_CMSSW_BASE"), os.getenv("CMT_CMSSW_VERSION"))
        
        if not os.getenv("_L1DSQCD"):
            os.environ["_L1DSQCD"] = "_L1DSQCD"

            ROOT.gSystem.Load("libL1DSModules.so")
            ROOT.gROOT.ProcessLine(".L {}/interface/QCDWeightCalc.h".format(base))
        
        if not os.getenv("_L1DSQCD_%s" % self.json):
            os.environ["_L1DSQCD_%s" % self.json] = "_L1DSQCD_%s" % self.json

            ROOT.gInterpreter.Declare("""
                auto qcd_weight%s = QCDWeightCalc("%s", %f);
            """ % (self.json, self.json_path, 30E6))

            # Function to calculate weights
            ROOT.gInterpreter.Declare("""
                using Vfloat = ROOT::RVec<float>;
                float get_qcd_weight_%s(
                    float genPtHat, Vfloat PileupPtHats 
                ){  
            
                    bool pass_em = false;
                    bool pass_mu = false;
                    std::vector<float> puPtHats;
                    for (int i = 0; i < PileupPtHats.size(); i++){
                        puPtHats.push_back(PileupPtHats[i]);
                    }
                    std::sort (puPtHats.begin(), puPtHats.end(), std::greater<float>());

                    return qcd_weight%s.weight(genPtHat, puPtHats, pass_em, pass_mu);
                    
                    //return 1.0;
                }
            """% (self.json, self.json))
    



    def run(self, df):
        #s = randomize("qcd_weight")

        df = df.Define(
            "qcd_weight", f"""get_qcd_weight_{self.json}(
                genPtHat, PileupPtHats
            )"""
        )

        #df = df.Define(
        #    "qcd_weight",
        #    "1.0"
        #)

        return df, ["qcd_weight"]



def QCDWeight(*args, **kwargs):
    return lambda: QCDWeightProducer(*args, **kwargs)