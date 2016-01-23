import re
from pypipboy import inventoryutils

class RadioControl():

    def __init__(self, pipdataManager , pipRootObj):
        self.currentRadioStation = None
        self.availableRadioStations = []
        self.pipRootObj = pipRootObj
        self.pipdataManager = pipdataManager
        if self.pipRootObj:
            self.pipRadioObject =  self.pipRootObj.child('Radio')
            if self.pipRadioObject:
                for i in range(0, self.pipRadioObject.childCount()):
                    station = self.pipRadioObject.child(i)
                    if station.child('inRange').value():
                        self.availableRadioStations.append(station)
                    if station.child('active').value():
                        self.currentRadioStation = station


    def changeStation(self, newstation):
        """
            -Changes station to newstation
        """
        strFound = False
        curKey = ""
        if self.pipRadioObject:
            for k in self.pipRadioObject.value():
                for x in k.value():
                    if x == 'text':
                        curName = k.child(x).value()
                        if curName.lower() == newstation.lower():
                            curKey = k.pipParentKey
                            strFound = True
        if strFound:

            curStation = self.pipRadioObject.child(curKey)
            inRange = self.pipRadioObject.child(curKey).child('inRange').value()
            if inRange:
                self.pipdataManager.rpcToggleRadioStation(curStation)
                data = "Tune to " + newstation + " Successful"
            else:
                data = "Station " + newstation + " is not in range"
        else:
            data = "Tune to " + newstation + " unSuccessful"
        return data

    def toggleRadio(self):
        print(self.pipdataManager)
        """Modified Code from hotkey.py  credit goes to  akamal """
        if (self.currentRadioStation):
                data = ('toggleRadio: currentstation: ' + self.currentRadioStation.child('text').value())
                self.pipdataManager.rpcToggleRadioStation(self.currentRadioStation)

        else:
            data = 'toggleRadio: no current, trying station First aviable station'
            numStations = len(self.availableRadioStations)
            if numStations > 0:
                self.pipdataManager.rpcToggleRadioStation(self.availableRadioStations[0])
        return data

    def nextStation(self):
        """Modified Code from hotkey.py  credit goes to  akamal """
        data = ""
        getIndex = 0
        numStations = len(self.availableRadioStations)
        if self.currentRadioStation:
            data =('nextRadio: currentstation: ' + self.currentRadioStation.child('text').value())
            for i in range (0, numStations):
                if self.availableRadioStations[i].child('text').value() == self.currentRadioStation.child('text').value():
                    getIndex = i + 1
                    break

        if (getIndex >= numStations):
            getIndex = 0

        if (getIndex <= numStations):
            txtResponse =('tuning radio to: ' + self.availableRadioStations[getIndex].child('text').value())
            self.pipdataManager.rpcToggleRadioStation(self.availableRadioStations[getIndex])

        return data

class InvetoryControl():
    """
    Used to control various inventory actions
    """

    def __init__(self, pipdataManager , pipRootObj ):
        """Constructor for InvetoryControl"""
        self.pipRootObj = pipRootObj
        self.pipdataManager = pipdataManager
        self.availableGrenades = []
        self.lastEquippedGrenade = ""
        self.availableMines = []
        self.lastEquippedMine = ""
        self.availableExplosives = []
        self.availableGuns = []
        self.lastEquippedGun = ""
        self.availableFavGuns = []
        self.lastEquippedFavGun = ""

        if self.pipRootObj:
            self.pipInventoryInfo = self.pipRootObj.child('Inventory')
            if (self.pipInventoryInfo):
                weapons = self.pipInventoryInfo.child('43')
                if(not weapons):
                    return
                for item in weapons.value():
                    equipped = False
                    favorite = False
                    name = item.child('text').value()
                    if inventoryutils.itemIsWeaponGun(item) and self.realWeaponCheck(item.pipId):
                        if (item.child('equipState').value() >0):
                            equipped = True
                            self.lastEquippedGun = name.lower()
                            if (item.child('favorite').value() >0 ): self.lastEquippedFavGun = name.lower()


                        if (item.child('favorite').value() >0 ): self.availableFavGuns.append([name.lower(), equipped])
                        self.availableGuns.append([name.lower(), equipped])
                    elif inventoryutils.itemIsWeaponMelee(item):
                        pass
                    elif inventoryutils.itemIsWeaponThrowable(item):
                        if (item.child('equipState').value() == 3):
                                equipped = True
                                self.lastEquippedExplosive = name.lower()
                        if (name.lower().find('grenade') > -1 or
                            name.lower().find('molotov') > -1):
                            if (item.child('equipState').value() == 3):
                                equipped = True
                                self.lastEquippedGrenade = name.lower()
                            self.availableGrenades.append([name.lower(), equipped])
                        if (name.lower().find('mine') > -1):
                            if (item.child('equipState').value() == 3):
                                equipped = True
                                self.lastEquippedMine = name.lower()
                            self.availableMines.append([name.lower(), equipped])
                self.availableExplosives = self.availableGrenades + self.availableMines

    def equipNextGun(self):
        """Modified Code from hotkey.py  credit goes to  akamal """
        data = ""
        nextIndex = -1
        lastIndex = -1
        self.availableGuns.sort()
        print(self.availableGuns)
        numGuns = len(self.availableGuns)
        if (numGuns > 0):
            for i in range(0, numGuns):
                if (self.availableGuns[i][1]):
                    nextIndex = i + 1
                    break
                if (self.availableGuns[i][0] == self.lastEquippedGun):
                    lastIndex = i
            if (nextIndex == numGuns):
                nextIndex = 0

            if (nextIndex < 0 and lastIndex >= 0):
                nextIndex = lastIndex

            if(nextIndex < 0):
                nextIndex = 0

            re1='(\\[).*?(\\])'
            re2='(\\().*?(\\))'
            re3='(\\{).*?(\\})'
            gunName = re.sub(re1,'',self.availableGuns[nextIndex][0])
            gunName = re.sub(re2,"",gunName)
            gunName = re.sub(re3,"",gunName).lstrip()
            self.useInventoryItemByName(gunName,"43")
            data = self.availableGuns[nextIndex][0]
        else:
            data = 'You have no Guns in your inventory'
        return data

    def equipNextFavGun(self):
        """Modified Code from hotkey.py  credit goes to  akamal """
        data = ""
        nextIndex = -1
        lastIndex = -1
        self.availableFavGuns.sort()
        print(self.availableFavGuns)
        numFavGuns = len(self.availableFavGuns)
        if (numFavGuns > 0):
            for i in range(0, numFavGuns):
                if (self.availableFavGuns[i][1]):
                    nextIndex = i + 1
                    break
                if (self.availableFavGuns[i][0] == self.lastEquippedFavGun):
                    lastIndex = i
            if (nextIndex == numFavGuns):
                nextIndex = 0

            if (nextIndex < 0 and lastIndex >= 0):
                nextIndex = lastIndex

            if(nextIndex < 0):
                nextIndex = 0

            re1='(\\[).*?(\\])'
            re2='(\\().*?(\\))'
            re3='(\\{).*?(\\})'
            gunName = re.sub(re1,'',self.availableFavGuns[nextIndex][0])
            gunName = re.sub(re2,"",gunName)
            gunName = re.sub(re3,"",gunName).lstrip()
            self.useInventoryItemByName(gunName,"43")
            data = self.availableFavGuns[nextIndex][0]
        else:
            data = 'You have no FavGuns in your inventory'
        return data

    def equipNextGrendae(self):
        """Modified Code from hotkey.py  credit goes to  akamal """
        data = ""
        nextIndex = -1
        lastIndex = -1
        self.availableGrenades.sort()
        numGrenades = len(self.availableGrenades)
        if (numGrenades > 0):
            for i in range(0, numGrenades):
                if (self.availableGrenades[i][1]):
                    nextIndex = i + 1
                    break
                if (self.availableGrenades[i][0] == self.lastEquippedGrenade):
                    lastIndex = i
            if (nextIndex == numGrenades):
                nextIndex = 0

            if (nextIndex < 0 and lastIndex >= 0):
                nextIndex = lastIndex

            if(nextIndex < 0):
                nextIndex = 0

            re1='(\\[).*?(\\])'
            re2='(\\().*?(\\))'
            re3='(\\{).*?(\\})'
            nadeName = re.sub(re1,'',self.availableGrenades[nextIndex][0])
            nadeName = re.sub(re2,"",nadeName)
            nadeName = re.sub(re3,"",nadeName).lstrip()
            self.useInventoryItemByName(nadeName,"43")
            data = self.availableGrenades[nextIndex][0]
        else:
            data = 'You have no grenades in your inventory'
        return data

    def equipNextMine(self):
        """Modified Code from hotkey.py  credit goes to  akamal """
        data = ""
        nextIndex = -1
        lastIndex = -1
        self.availableMines.sort()
        numMinees = len(self.availableMines)
        if (numMinees > 0):
            for i in range(0, numMinees):
                if (self.availableMines[i][1]):
                    nextIndex = i + 1
                    break
                if (self.availableMines[i][0] == self.lastEquippedMine):
                    lastIndex = i
            if (nextIndex == numMinees):
                nextIndex = 0

            if (nextIndex < 0 and lastIndex >= 0):
                nextIndex = lastIndex

            if(nextIndex < 0):
                nextIndex = 0

            re1='(\\[).*?(\\])'
            re2='(\\().*?(\\))'
            re3='(\\{).*?(\\})'
            mineName = re.sub(re1,'',self.availableMines[nextIndex][0])
            mineName = re.sub(re2,"",mineName)
            mineName = re.sub(re3,"",mineName).lstrip()
            self.useInventoryItemByName(mineName,"43")
            data = self.availableMines[nextIndex][0]
        else:
            data = 'You have no Mines in your inventory'
        return data

    def equipNextExplosive(self):
        """Modified Code from hotkey.py  credit goes to  akamal """
        data = ""
        nextIndex = -1
        lastIndex = -1
        self.availableExplosives.sort()
        numExplosives = len(self.availableExplosives)
        if (numExplosives > 0):
            for i in range(0, numExplosives):
                if (self.availableExplosives[i][1]):
                    nextIndex = i + 1
                    break
                if (self.availableExplosives[i][0] == self.lastEquippedExplosive):
                    lastIndex = i
            if (nextIndex == numExplosives):
                nextIndex = 0

            if (nextIndex < 0 and lastIndex >= 0):
                nextIndex = lastIndex

            if(nextIndex < 0):
                nextIndex = 0

            re1='(\\[).*?(\\])'
            re2='(\\().*?(\\))'
            re3='(\\{).*?(\\})'
            nadeName = re.sub(re1,'',self.availableExplosives[nextIndex][0])
            nadeName = re.sub(re2,"",nadeName)
            nadeName = re.sub(re3,"",nadeName).lstrip()
            self.useInventoryItemByName(nadeName,"43")
            data = self.availableExplosives[nextIndex][0]
        else:
            data = 'You have no grenades in your inventory'
        return data

    def useInventoryItemByName(self, itemName, inventorySection):
        """Modified Code from hotkey.py  credit goes to  akamal """

        re1='(\\[).*?(\\])'
        re2='(\\().*?(\\))'
        re3='(\\{).*?(\\})'
        data = ""
        itemName = itemName.lower()
        if self.pipInventoryInfo:
            inventory = self.pipInventoryInfo.child(inventorySection)
            for i in range(0, inventory.childCount()):
                name = re.sub(re1,'',inventory.child(i).child('text').value())
                name = re.sub(re2,"",name)
                name = re.sub(re3,"",name)

                if name.lower().lstrip() == itemName:
                    if self.realWeaponCheck(inventory.child(i).pipId):
                        self.pipdataManager.rpcUseItem(inventory.child(i))
                        data = itemName
                        return data

            data = 'Could not find %s in your inventory' %  itemName
        return data

    def realWeaponCheck(self, pipId):
        """
        Will check if weapon is real one by seeing if it's pipID is in sortID list.
        Args: pipID: ID of weapon to check

        Returns:True/False
        """
        if self.pipInventoryInfo:
            self.sortedIDS = []
            sortedIDInfo = self.pipInventoryInfo.child('sortedIDS')
            for k in sortedIDInfo.value():
               self.sortedIDS.append(k.value())
            if pipId in self.sortedIDS:
                return True


class MapControl():
    """
    Controls various map functions.
    """

    def __init__(self, pipdataManager , pipRootObj ):
        """Constructor for MapControl"""
        self.pipdataManager = pipdataManager
        self.pipRootObj = pipRootObj

    def onFastTravel(self, sName):
            """
                 Takes the sent map location name(sName) and issues fast travel rpc command to go there
                And returns a stauts message to VA
            Args:
                sName:

            Returns:

            """
            strFound = False
            data = ""
            curKey = ""
            if self.pipRootObj:
                pipMapObject = self.pipRootObj.child('Map')
                pipMapWorldObject = pipMapObject.child('World')
                if pipMapWorldObject:
                    pipWorldLocations = pipMapWorldObject.child('Locations')
                    if pipWorldLocations:
                        for k in pipWorldLocations.value():
                            for x in k.value():
                                if x == 'Name':
                                    curName = k.child(x).value()
                                    if curName.lower() == sName.lower():
                                        curKey = k.pipParentKey
                                        strFound = True
                    if strFound:
                        curPoint = pipWorldLocations.child(curKey)
                        discovered = pipWorldLocations.child(curKey).child('Discovered').value()
                        if discovered:
                            self.pipdataManager.rpcFastTravel(curPoint)
                            data = "Fast Travel Location " + sName + " Successful"
                        else:
                            data = "Location " + sName + " Has Not Been Discovered yet"
                    else:
                       data = "Fast Travel Location " + sName + " unSuccessful"
                return data

    def getDirections(self, sName):
        """
        Args:
            sName: Name of location or quest sent from VA
            sType: either LocationDirections or QuestDirections to determine type of location lookup

        Returns:
            compass_direction in a english response
        """
        curKey = False
        if self.pipRootObj:
                strFound = False
                curKey = ""
                pipMapObject = self.pipRootObj.child('Map')
                pipMapWorldObject = pipMapObject.child('World')
                if pipMapWorldObject:
                    pipPlayerLocation = pipMapWorldObject.child('Player')
                    pipLocations = pipMapWorldObject.child('Locations')

                    for k in pipLocations.value():
                            for x in k.value():
                                if x == 'Name':
                                    curName = k.child(x).value()
                                    if curName.lower() == sName.lower():
                                        curKey = k.pipParentKey
                                        strFound = True
                if strFound:
                    ToLocation = pipLocations.child(curKey)
                    PlayerY = float(pipPlayerLocation.child('Y').value())
                    PlayerX = float(pipPlayerLocation.child('X').value())
                    LocationX = float(ToLocation.child('X').value())
                    LocationY = float(ToLocation.child('Y').value())

                    from math import degrees, atan2,hypot

                    angle = degrees(atan2(LocationY - PlayerY, LocationX - PlayerX))
                    bearing = (90 - angle) % 360
                    dirs = [
                            "North", "North by northEast", "North East", "East by NorthEast", "East",
                            "East by SouthEast", "SouthEast", "South by SouthEast", "South", "South by SouthWest",
                            "SouthWest", "West by SouthWest", "West", "WestNorthWest", "NorthWest", "North by NorthWest"
                            ]
                    ix = int((bearing + 11.25)/22.5)
                    dist = hypot(LocationX - PlayerX, LocationY - PlayerY)
                    compass_direction = (dirs[ix % 16])
                    data = compass_direction
                    return data


    def placeCustomMarker(self, sName, sOverRide):
        curKey = False
        data = ""
        if self.pipRootObj:
                strFound = False
                curKey = ""
                pipMapObject = self.pipRootObj.child('Map')
                pipMapWorldObject = pipMapObject.child('World')
                if pipMapWorldObject:
                    pipLocations = pipMapWorldObject.child('Locations')

                    for k in pipLocations.value():
                            for x in k.value():
                                if x == 'Name':
                                    curName = k.child(x).value()
                                    if curName.lower() == sName.lower():
                                        curKey = k.pipParentKey
                                        strFound = True
                if strFound:
                    print("o2")
                    ToLocation = pipLocations.child(curKey)
                    LocationX = float(ToLocation.child('X').value())
                    LocationY = float(ToLocation.child('Y').value())

                    discovered = ToLocation.child('Discovered').value()
                    if discovered or sOverRide:
                        print("ok")
                        self.pipdataManager.rpcSetCustomMarker(LocationX, LocationY)
                        data = "Marker placed at %s,%s"% (str(LocationX),str(LocationY))
                    else:
                        data = "Location Not Discovered"
                else:
                    data = 'Location Not Found'
        return data

    def removeMarker(self):
        """

        Args:


        Returns:

        """
        self.pipdataManager.rpcRemoveCustomMarker()
        data = "Marker Deleted"
        return data
