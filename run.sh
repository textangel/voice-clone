source /Users/mismus/miniforge3/etc/profile.d/conda.sh
conda activate elevenlabs

say "Now Running Voice Cloning"
while true; do
    python elevenlabs-clone.py
    [ $? -eq 0 ] && break
done