# Meshcore-Signal-Heatmap
### Meshcore Signal Heatmap – Plain-Language Description

**Goal**  
Add a new map layer to the Meshcore app that shows where the network signal is strong or weak. The layer looks like a heatmap (warm colors = strong signal, cool colors = weak signal).

**The proposal (for now)**

- Devices in the Meshcore network send short “ping” messages to each other. Each reply includes how strong the signal is.
- Whenever a device sends or receives a ping, it notes:
  - How strong and clear the signal was
  - Which device it came from and went to
  - When and where it happened
  - What gear was used (radio model, antenna type, power setting)
- These notes are stored on the device until they can be shared. Later, they sync to a main node or server that collects everyone’s data.
- The server blends all the points together to make a smooth heatmap for the map view. You can filter by time, device type, or antenna to compare setups.

**In the Meshcore app (meshcore app developers to take responsibility for this)**

- A new toggle in the map view turns the heatmap on or off.
- You can adjust how see-through it is and which signal measurement you want to look at.
- You can filter the map to focus on certain antennas, radios, or time ranges.
- Tapping an area can show more details, like average signal strength or recent pings.
- You can export the data if you want to run your own analysis.

**Why it helps**

- See coverage gaps quickly—handy for planning new nodes or moving gear.
- Compare antennas or mounting styles to find out what works best.
- Fix problems faster by spotting weak links in the network.
- Share clear visuals with team members or partners.

**Practical safeguards**

- Pings are spaced out so they don’t overload the network.
- Devices skip data collection if their battery is low or if the network is already busy.
- Collected info follows the same privacy rules Meshcore already uses; devices can opt out.

**What to build**

1. Add ping-logging that remembers signal strength plus device/antenna details.
2. Add a sync process so devices upload their data when they can.
3. Create a service that turns the collected data into heatmap tiles.
4. Update the app to show the heatmap and let users control it.
5. Write setup and user guides explaining how the new feature works and how to interpret it.
