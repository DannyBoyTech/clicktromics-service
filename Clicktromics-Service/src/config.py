import os
import sys
from src.logger import Logger
from pathlib import Path


log = Logger.get_logger()
current_file_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(current_file_path)
root_directory = os.path.abspath(os.path.join(parent_directory, ".."))

ENV="LOCAL"

JOB_QUEUE_ARN_GPU=os.getenv('JOB_QUEUE_ARN_GPU')
JOB_QUEUE_ARN_CPU=os.getenv('JOB_QUEUE_ARN_CPU')
JOB_QUEUE_ARN_TEST=os.getenv('JOB_QUEUE_ARN_TEST')
JOB_DEFINITION_ARN_BOLTZ=os.getenv('JOB_DEFINITION_ARN_BOLTZ')
JOB_DEFINITION_ARN_DIFFAB=os.getenv('JOB_DEFINITION_ARN_DIFFAB')
JOB_DEFINITION_ARN_TEST=os.getenv('JOB_DEFINITION_ARN_TEST')
JOB_DEFINITION_ARN_HOMELETTE=os.getenv('JOB_DEFINITION_ARN_HOMELETTE')
JOB_DEFINITION_ARN_MUSITE=os.getenv('JOB_DEFINITION_ARN_MUSITE')
JOB_DEFINITION_ARN_GNINA=os.getenv('JOB_DEFINITION_ARN_GNINA')
JOB_DEFINITION_ARN_GAN=os.getenv('JOB_DEFINITION_ARN_GAN')
JOB_DEFINITION_ARN_BLOOD_TEST=os.getenv('JOB_DEFINITION_ARN_BLOOD_TEST')
JOB_DEFINITION_ARN_URL_DOWNLOAD=os.getenv('JOB_DEFINITION_ARN_URL_DOWNLOAD')
JOB_DEFINITION_ARN_VEP_ENSEMBLE=os.getenv('JOB_DEFINITION_ARN_VEP_ENSEMBLE')
JOB_DEFINITION_ARN_BAM_PROCESSING=os.getenv('JOB_DEFINITION_ARN_BAM_PROCESSING')
JOB_DEFINITION_ARN_FASTQ_PROCESSING=os.getenv('JOB_DEFINITION_ARN_FASTQ_PROCESSING')
JOB_DEFINITION_ARN_MICROBIOME=os.getenv('JOB_DEFINITION_ARN_MICROBIOME')
JOB_DEFINITION_ARN_GENETIC_ANNOTATION=os.getenv('JOB_DEFINITION_ARN_GENETIC_ANNOTATION')
JOB_DEFINITION_ARN_GENETIC=os.getenv('JOB_DEFINITION_ARN_GENETIC')


AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', "eu-west-1")

DEFAULT_BUCKET_NAME = os.getenv('DEFAULT_BUCKET_NAME', 'clicktromics')
USE_LOCAL_STORAGE=os.getenv("USE_LOCAL_STORAGE", "")
USE_AWS=os.getenv("USE_AWS", False)
LOCAL_STORAGE_PATH=os.getenv("LOCAL_STORAGE_PATH")
DEFAULT_VOLUME_NAME = os.getenv('DEFAULT_VOLUME_NAME', 'dt-file-backup')

ALLOW_ORIGINS=os.getenv("ALLOW_ORIGINS")

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")
MONGO_URL = os.getenv("MONGO_URL")
MONGO_DATABASE = "genetiq"

RCSB_URL = "https://files.rcsb.org/download/"

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

REDIS_URL_BROKER = "redis://:" + REDIS_PASSWORD +  "@" + REDIS_HOST + ":" + REDIS_PORT + "/0"
REDIS_URL_BACKEND = "redis://:" + REDIS_PASSWORD +  "@" + REDIS_HOST + ":" + REDIS_PORT + "/1"

DEFAULT_SMILES = "CC1C2CC(C(C=CC=C(CC3=CC(=C(C(=C3)OC)Cl)N(C(=O)CC(C4(C1O4)C)OC(=O)C(C)N(C)C(=O)CCC(C)(C)S)C)C)OC)(NC(=O)O2)O"
DEFAULT_SEQUENCE = "MNKHKKGSIFGIIGLVVIFAVVSFLFFSMISDQIFFKHVKSDIKIEKLNVTLNDAAKKQINNYTSQQVSNKKNDAWRDASATEIKSAMDSGTFIDNEKQKYQFLDLSKYQGIDKNRIKRMLVDRPTLLKHTDDFLKAAKDKHVNEVYLISHALLETGAVKSELANGVEIDGKKYYNFYGVGALDKDPIKTGAEYAKKHGWDTPEKAISGGADFIHKHFLSSTDQNTLY"
CPU_THRESHOLD = 60
RAM_THRESHOLD = 70

SMART_REACTION = {
    "SPACC": "[#6:7][C:6]#[C:5].[A:4][#7:3]-[N:2]=[#7:1]>>[A:4]-[#7:3]-1-[#6:5]=[#6:6](-[#6:7])-[#7:1]=[#7:2]-1"
}
GLYCAN_LINKER = { "Azide":"N=N-N(*)"}

LINKERS = {
    "DBCO-acid": "O=C(CCC(O(*))=O)N(C1)C2=C(C=CC=C2)C#CC3=C1C=CC=C3",
    "BCN-acid": "O(*)C(=O)CCC(=O)C1C2CCC#CCCC12",
    "DBCO-PEG1-OH":"O=C(CCC(N1C2=C(C#CC3=C(C1)C=CC=C3)C=CC=C2)=O)NCCOCCO(*)",
    "DBCO-PEG1-acid": "O=C(N1CC2=C(C#CC3=C1C=CC=C3)C=CC=C2)CCC(NCCOCCC(O(*))=O)=O",
    "BCN-PEG1-OH":"[H][C@]12[C@](CCC#CCC2)([H])[C@@H]1COC(NCCOCCO(*))=O",
    "BCN-PEG1-acid":"O=C(CCOCCNC(OCC1C2CCC#CCCC12)=O)O(*)",
    "DBCO-S-S-acid": "O=C(CCC(NCCSSCCC(O(*))=O)=O)N1C(C=CC=C2)=C2C#CC(C=CC=C3)=C3C1"
}
GLYCANS =    {
    "Neu5Ac(a2-3)Gal(b1-4)[D-Fuc(a1-3)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O[C@H]4O[C@H](C)[C@H](O)[C@H](O)[C@H]4O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-6)Gal(b1-4)[Fuc(a1-3)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2O[C@@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@H](O)[C@@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac9Ac(a2-3)Gal(a1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)COC(C)=O)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O)[C@@H](CO)OC[C@@H]3NC(C)=O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-6)Gal(a1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2O[C@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@H](O)[C@@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-2)Gal(b1-3)[Fuc(a1-4)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](CO)OC[C@@H]3NC(C)=O)O[C@H](CO)[C@H](O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-6)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2OC[C@H](NC(C)=O)[C@@H](O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac4Ac(a2-3)Gal(b1-4)[Fuc(a1-3)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1OC(C)=O",
            "Neu5Ac(a2-3)Gal(b1-4)Fuc(a1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@@H](O)[C@H](O)[C@H](O[C@H]4[C@H](O)[C@@H](CO)OC[C@@H]4NC(C)=O)O[C@H]3C)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac9Ac(a2-3)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)COC(C)=O)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac7Ac(a2-3)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](OC(C)=O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-6)[Fuc(a1-2)]Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@H](O[C@@H]3O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]3O)[C@@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(a1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@H](O[C@H]3[C@H](O)[C@@H](CO)OC[C@@H]3NC(C)=O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Glc(b1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@@H]2[C@@H](O)[C@H](O[C@H]3[C@H](O)[C@@H](CO)OC[C@@H]3NC(C)=O)O[C@H](CO)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-3)[D-Fuc(a1-4)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O[C@H]4O[C@H](C)[C@H](O)[C@H](O)[C@H]4O)[C@@H](CO)OC[C@@H]3NC(C)=O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(b2-3)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(a1-3)[Rha(a1-4)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@H](O)[C@@H](O)[C@H]4O)[C@@H](CO)OC[C@@H]3NC(C)=O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-3)[Neu5Ac(a2-6)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2OC[C@H](NC(C)=O)[C@@H](O[C@@H]3O[C@H](CO)[C@H](O)[C@H](O[C@]4(C(=O)O(*))C[C@H](O)[C@@H](NC(C)=O)[C@H]([C@H](O)[C@H](O)CO)O4)[C@H]3O)[C@@H]2O)(C(=O)O)C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-4)Fuc(b1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@@H](O)[C@H](O)[C@@H](O[C@H]4[C@H](O)[C@@H](CO)OC[C@@H]4NC(C)=O)O[C@H]3C)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-3)Fuc(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O)[C@@H](O[C@H]4[C@H](O)[C@@H](NC(C)=O)CO[C@@H]4CO)O[C@@H](C)[C@H]3O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac9Ac(a2-3)Gal(b1-3)[Fuc(a1-4)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)COC(C)=O)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](CO)OC[C@@H]3NC(C)=O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(a1-3)[Fuc(a1-4)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](CO)OC[C@@H]3NC(C)=O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-8)Neu5Ac(a2-6)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H](CO)[C@@H](O)[C@@H]2O[C@@](OC[C@H]3O[C@@H](O[C@H]4[C@H](O)[C@@H](NC(C)=O)CO[C@@H]4CO)[C@H](O)[C@@H](O)[C@H]3O)(C(=O)O)C[C@H](O)[C@H]2NC(C)=O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac9Ac(a2-3)Gal(b1-4)[Fuc(a1-3)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)COC(C)=O)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac9N(a2-3)Gal(b1-4)[Fuc(a1-3)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CN)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac9Ac(a2-6)Gal(b1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)COC(C)=O)O[C@@](OC[C@H]2O[C@@H](O[C@H]3[C@H](O)[C@@H](CO)OC[C@@H]3NC(C)=O)[C@H](O)[C@@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal2F(b1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O)[C@@H](CO)OC[C@@H]3NC(C)=O)[C@@H]2F)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac7Ac(a2-3)Gal(a1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](OC(C)=O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-4)Gal(b1-3)[Neu5Ac(a2-6)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2OC[C@H](NC(C)=O)[C@@H](O[C@@H]3O[C@H](CO)[C@H](O[C@]4(C(=O)O(*))C[C@H](O)[C@@H](NC(C)=O)[C@H]([C@H](O)[C@H](O)CO)O4)[C@H](O)[C@H]3O)[C@@H]2O)(C(=O)O)C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-6)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](OC[C@H]3OC[C@H](NC(C)=O)[C@@H](O)[C@@H]3O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(b2-6)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@](OC[C@H]2O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@H](O)[C@@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(b2-6)Gul(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@](OC[C@H]2O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@H](O)[C@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-4)[Fuc(a1-3)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-8)Neu5Gc(a2-3)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H](CO)[C@@H](O)[C@@H]2O[C@@](O[C@H]3[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]4[C@H](O)[C@@H](NC(C)=O)CO[C@@H]4CO)[C@@H]3O)(C(=O)O)C[C@H](O)[C@H]2NC(=O)CO)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac4Ac(a2-3)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1OC(C)=O",
            "Neu5Ac(a2-8)Neu5Ac(a2-3)Gal(b1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H](CO)[C@@H](O)[C@@H]2O[C@@](O[C@H]3[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]4[C@H](O)[C@@H](CO)OC[C@@H]4NC(C)=O)[C@@H]3O)(C(=O)O)C[C@H](O)[C@H]2NC(C)=O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-4)[Fuc(b1-3)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O[C@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-9)Neu5Ac(a2-3)Gal(b1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@@H](O)[C@@H](O)[C@@H]2O[C@@](O[C@H]3[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]4[C@H](O)[C@@H](CO)OC[C@@H]4NC(C)=O)[C@@H]3O)(C(=O)O)C[C@H](O)[C@H]2NC(C)=O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(b2-9)Neu5Ac(b2-3)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@](OC[C@@H](O)[C@@H](O)[C@@H]2O[C@](O[C@H]3[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]4[C@H](O)[C@@H](NC(C)=O)CO[C@@H]4CO)[C@@H]3O)(C(=O)O)C[C@H](O)[C@H]2NC(C)=O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(a1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-3)[Neu5Ac(a2-3)Gal(b1-4)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O[C@@H]4O[C@H](CO)[C@H](O)[C@H](O[C@]5(C(=O)O)C[C@H](O)[C@@H](NC(C)=O)[C@H]([C@H](O)[C@H](O)CO)O5)[C@H]4O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-4)[Gal3Me(b1-4)Glc(b1-6)]GlcNAc": "CO[C@H]1[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]2[C@H](O)[C@@H](O)[C@H](OC[C@H]3OC[C@H](NC(C)=O)[C@@H](O)[C@@H]3O[C@@H]3O[C@H](CO)[C@H](O)[C@H](O[C@]4(C(=O)O(*))C[C@H](O)[C@@H](NC(C)=O)[C@H]([C@H](O)[C@H](O)CO)O4)[C@H]3O)O[C@@H]2CO)[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-4)[Gal(b1-6)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO[C@@H]3O[C@H](CO)[C@H](O)[C@H](O)[C@H]3O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-2)[Neu5Ac(a2-3)]Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)O[C@H](CO)[C@H](O)[C@@H]2O[C@]2(C(=O)O(*))C[C@H](O)[C@@H](NC(C)=O)[C@H]([C@H](O)[C@H](O)CO)O2)(C(=O)O)C[C@@H]1O",
            "Neu5Ac(a2-8)Neu5Ac(a2-8)Neu5Ac(a2-3)Gal(b1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H](CO)[C@@H](O)[C@@H]2O[C@@](O[C@H](CO)[C@@H](O)[C@@H]3O[C@@](O[C@H]4[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]5[C@H](O)[C@@H](CO)OC[C@@H]5NC(C)=O)[C@@H]4O)(C(=O)O)C[C@H](O)[C@H]3NC(C)=O)(C(=O)O)C[C@H](O)[C@H]2NC(C)=O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-4)[Fuc2Me(a1-3)]GlcNAc": "CO[C@@H]1[C@H](O[C@H]2[C@H](O[C@@H]3O[C@H](CO)[C@H](O)[C@H](O[C@]4(C(=O)O(*))C[C@H](O)[C@@H](NC(C)=O)[C@H]([C@H](O)[C@H](O)CO)O4)[C@H]3O)[C@@H](CO)OC[C@@H]2NC(C)=O)O[C@@H](C)[C@@H](O)[C@H]1O",
            "Neu5Ac(a2-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@H](O)[C@@H](CO)OC[C@@H]2NC(C)=O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac9Ac(a2-3)Gal(b1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)COC(C)=O)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O)[C@@H](CO)OC[C@@H]3NC(C)=O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-3)[Fuc(a1-4)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](CO)OC[C@@H]3NC(C)=O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac9Ac(a2-6)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)COC(C)=O)O[C@@](OC[C@H]2O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@H](O)[C@@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-4)[Fuc(a1-6)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO[C@@H]3O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]3O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-3)[Neu5Ac(a2-6)][Fuc(a1-4)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2OC[C@H](NC(C)=O)[C@@H](O[C@@H]3O[C@H](CO)[C@H](O)[C@H](O[C@]4(C(=O)O(*))C[C@H](O)[C@@H](NC(C)=O)[C@H]([C@H](O)[C@H](O)CO)O4)[C@H]3O)[C@@H]2O[C@@H]2O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]2O)(C(=O)O)C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(b1-4)[Gal(b1-4)Glc(b1-6)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO[C@@H]3O[C@H](CO)[C@H](O[C@@H]4O[C@H](CO)[C@H](O)[C@H](O)[C@H]4O)[C@H](O)[C@H]3O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-6)Glc(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@H](O)[C@@H](O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal2F(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2F)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-6)Gal(b1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2O[C@@H](O[C@H]3[C@H](O)[C@@H](CO)OC[C@@H]3NC(C)=O)[C@H](O)[C@@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-6)Gal(b1-3)[Fuc(a1-4)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2O[C@@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](CO)OC[C@@H]3NC(C)=O)[C@H](O)[C@@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-6)Gal(b1-6)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2O[C@@H](OC[C@H]3OC[C@H](NC(C)=O)[C@@H](O)[C@@H]3O)[C@H](O)[C@@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal6F(b1-4)[Fuc(a1-3)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CF)O[C@@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-4)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@@H]2[C@H](O)[C@@H](O)[C@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)O[C@@H]2CO)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-6)Man(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H](O)[C@@H](O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Man(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@@H]2[C@H](O)[C@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)O[C@H](CO)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-2)Gal(b1-4)[Fuc(a1-3)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](NC(C)=O)CO[C@@H]3CO)O[C@H](CO)[C@H](O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal(a1-4)[Fuc(a1-3)]GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H]2[C@@H](O)[C@@H](CO)O[C@H](O[C@H]3[C@H](O[C@@H]4O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]4O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-6)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@H](O)[C@@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac7Ac(a2-6)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](OC(C)=O)[C@H](O)CO)O[C@@](OC[C@H]2O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@H](O)[C@@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-6)Gal(b1-6)Gal(b1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](OC[C@H]2O[C@@H](OC[C@H]3O[C@@H](O[C@H]4[C@H](O)[C@@H](CO)OC[C@@H]4NC(C)=O)[C@H](O)[C@@H](O)[C@H]3O)[C@H](O)[C@@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)Gal2Me(b1-3)GlcNAc": "CO[C@H]1[C@H](O[C@H]2[C@H](O)[C@@H](CO)OC[C@@H]2NC(C)=O)O[C@H](CO)[C@H](O)[C@@H]1O[C@]1(C(=O)O(*))C[C@H](O)[C@@H](NC(C)=O)[C@H]([C@H](O)[C@H](O)CO)O1",
            "Neu5Ac9N(a2-6)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CN)O[C@@](OC[C@H]2O[C@@H](O[C@H]3[C@H](O)[C@@H](NC(C)=O)CO[C@@H]3CO)[C@H](O)[C@@H](O)[C@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-3)[Fuc(a1-4)]Gal(b1-3)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@@H]2[C@@H](O)[C@H](O[C@H]3[C@H](O)[C@@H](CO)OC[C@@H]3NC(C)=O)O[C@H](CO)[C@@H]2O[C@@H]2O[C@@H](C)[C@@H](O)[C@@H](O)[C@@H]2O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-8)Neu5Ac(a2-3)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H](CO)[C@@H](O)[C@@H]2O[C@@](O[C@H]3[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]4[C@H](O)[C@@H](NC(C)=O)CO[C@@H]4CO)[C@@H]3O)(C(=O)O)C[C@H](O)[C@H]2NC(C)=O)(C(=O)O(*))C[C@@H]1O",
            "Neu5Ac(a2-8)Neu5Ac(a2-8)Neu5Ac(a2-3)Gal(b1-4)GlcNAc": "CC(=O)N[C@H]1[C@H]([C@H](O)[C@H](O)CO)O[C@@](O[C@H](CO)[C@@H](O)[C@@H]2O[C@@](O[C@H](CO)[C@@H](O)[C@@H]3O[C@@](O[C@H]4[C@@H](O)[C@@H](CO)O[C@@H](O[C@H]5[C@H](O)[C@@H](NC(C)=O)CO[C@@H]5CO)[C@@H]4O)(C(=O)O)C[C@H](O)[C@H]3NC(C)=O)(C(=O)O)C[C@H](O)[C@H]2NC(C)=O)(C(=O)O(*))C[C@@H]1O"
}

missing_vars = []

# if not AWS_ACCESS_KEY:
#     missing_vars.append("AWS_ACCESS_KEY")
# if not AWS_SECRET_KEY:
#     missing_vars.append("AWS_SECRET_KEY")
if not REDIS_HOST:
    missing_vars.append("REDIS_HOST")
if not REDIS_PORT:
    missing_vars.append("REDIS_PORT")
if not MONGO_URL:
    missing_vars.append("MONGO_URL")
if not ALLOW_ORIGINS:
    missing_vars.append("ALLOW_ORIGINS")

if missing_vars:
    log.debug(f"Error: Missing environment variables - {', '.join(missing_vars)}")
    sys.exit(1)

log.info("All required environment variables are set.")