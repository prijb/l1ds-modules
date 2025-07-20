# pT regression for jets using a BDT
import os

from analysis_tools.utils import import_root, randomize
from Base.Modules.baseModules import JetLepMetSyst

ROOT = import_root()

class L1DSBDTJetProducer(JetLepMetSyst):
    def __init__(self, *args, **kwargs):
        default_name = "bdt_regression_l1ds"
        use_sigmoid = "false"
        #use_sigmoid = "true"

        default_model_path = os.path.expandvars("$CMSSW_BASE/src/L1DS/Modules/data/bdt_model_qcd_15to7000.json")

        self.model_path = kwargs.pop("model_path", default_model_path)
        self.model = self.model_path.replace("/", "_").replace(".", "_")
        self.bdt_name = kwargs.pop("bdt_name", default_name)

        super(L1DSBDTJetProducer, self).__init__(*args, **kwargs)

        base = "{}/{}/src/L1DS/Modules".format(
            os.getenv("CMT_CMSSW_BASE"), os.getenv("CMT_CMSSW_VERSION"))

        if not os.getenv("_L1DSBDT"):
            os.environ["_L1DSBDT"] = "_L1DSBDT"

            ROOT.gSystem.Load("libL1DSModules.so")
            ROOT.gROOT.ProcessLine(".L {}/interface/BDTJetRegression.h".format(base))

        if not os.getenv("_L1DSBDT_%s" % self.model):
            os.environ["_L1DSBDT_%s" % self.model] = "_L1DSBDT_%s" % self.model

            ROOT.gInterpreter.Declare("""
                auto bdt%s = BDTJetRegression("%s", %s);
            """ % (self.model, self.model_path, use_sigmoid)
            )

            ROOT.gInterpreter.Declare("""
                using Vfloat = ROOT::RVec<float>;
                using Vint = ROOT::RVec<int>;

                std::vector<float> get_regressed_jet_pt(
                    Vfloat Jet_pt, Vfloat Jet_eta, Vfloat Jet_phi, Vfloat EGamma_pt, Vfloat EGamma_eta, Vfloat EGamma_phi, Vfloat Muon_pt, Vfloat Muon_etaAtVtx, Vfloat Muon_phiAtVtx
                ){
                    std::vector<float> regressed_jet_pt_vector(Jet_pt.size(), 0.0);

                    for (int i = 0; i < Jet_pt.size(); i++){
                        float regressed_pt = 0.0;
                        float egamma_pt_sum = 0.0;
                        float egamma_rel_iso = 0.0;
                        float muon_pt_sum = 0.0;
                        float muon_rel_iso = 0.0;
                        float dphi = 0.0;
                        float deta = 0.0;
                        float dr = 0.0;
                        
                        // Sum over the EGamma candidates
                        for (int i_egamma = 0; i_egamma < EGamma_pt.size(); i_egamma++) {
                            dphi = TVector2::Phi_mpi_pi(Jet_phi[i] - EGamma_phi[i_egamma]);
                            deta = Jet_eta[i] - EGamma_eta[i_egamma];
                            dr = std::sqrt(dphi*dphi + deta*deta);
                            if (dr < 0.4) {
                                egamma_pt_sum += EGamma_pt[i_egamma];
                            }
                        }

                        // Sum over the Muon candidates
                        for (int i_muon = 0; i_muon < Muon_pt.size(); i_muon++) {
                            dphi = TVector2::Phi_mpi_pi(Jet_phi[i] - Muon_phiAtVtx[i_muon]);
                            deta = Jet_eta[i] - Muon_etaAtVtx[i_muon];
                            dr = std::sqrt(dphi*dphi + deta*deta);
                            if (dr < 0.4) {
                                muon_pt_sum += Muon_pt[i_muon];
                            }
                        }

                        egamma_rel_iso = egamma_pt_sum/Jet_pt[i]; 
                        muon_rel_iso = muon_pt_sum/Jet_pt[i];

                        regressed_pt = bdt%s.get_regressed_pt(
                            {Jet_pt[i], Jet_eta[i], Jet_phi[i],
                            egamma_rel_iso, muon_rel_iso}
                        );
                        regressed_pt = regressed_pt * Jet_pt[i];
                                      
                        //std::cout << "Jet with inputs: " <<
                        //" pt: " << Jet_pt[i] << 
                        //" eta: " << Jet_eta[i] <<
                        //" phi: " << Jet_phi[i] <<
                        //" EGamma rel iso: " << egamma_rel_iso <<
                        //" Muon rel iso: " << muon_rel_iso <<
                        //" regressed pt: " << regressed_pt << std::endl;

                        regressed_jet_pt_vector[i] = regressed_pt;                     
                    }
                    return regressed_jet_pt_vector;
                }
            """ % (self.model)
            )

    def run(self, df):
        df = df.Define("Jet_pt_regressed", f"""get_regressed_jet_pt(
            Jet_pt, Jet_eta, Jet_phi, 
            EGamma_pt, EGamma_eta, EGamma_phi, 
            Muon_pt, Muon_etaAtVtx, Muon_phiAtVtx
        )"""
        )

        return df, ["Jet_pt_regressed"]

def L1DSBDTJet(*args, **kwargs):
    return lambda: L1DSBDTJetProducer(*args, **kwargs)

