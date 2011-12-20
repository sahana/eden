from base import Element, PositionableElement, BoxElement
from group import Grouping
from defs import Symbol, Use
from utils import ViewBox

from ..utils.struct import Vector as V, Matrix
from math import sqrt, cos, sin


from copy import deepcopy


class Circle (PositionableElement):
    def __init__ (self, **attr):
        PositionableElement.__init__ (self, name = 'circle', **attr)
        if attr.has_key ('radius'):
            self.radius = attr['radius']
        else:
            self.radius = 0.0

    def size (self, value):
        self.radius = value

    def setSVG (self):
        pos = V (self.x, self.y)
        self.applyTransform (pos)
        attr = PositionableElement.setSVG (self) 
        attr.update ([('cx', pos.x), 
                      ('cy', pos.y),
                      ('r', self.radius)])
        return attr

class PathElement:
    def matrix (self):
        return Matrix (3, 1, [self.x, self.y, 1])

class AnchorElement (PathElement):
    def __init__ (self, x, y):
        self.x = x
        self.y = y

    def __str__ (self):
        return ' '.join (['M'] + map (str, [self.x, self.y])) 

class LinearElement (PathElement):
    def __init__ (self, x, y):
        self.x = x
        self.y = y

    def __str__ (self):
        return ' '.join (['L'] + map (str, [self.x, self.y])) 

class CloseElement (PathElement):
    def __init__ (self):
        pass

    def __str__ (self):
        return 'Z'

class Path (PositionableElement):
    def __init__ (self, **attr):
        PositionableElement.__init__ (self, name = 'path', **attr)
        if attr.has_key ('transform'):
            self.postTransform = attr['transform']
        else:
            self.postTransform = None
        self.elements = []
        self.closed = False

    def line (self, x, y):
        self.elements.append (LinearElement (x, y))

    def move (self, x, y):
        self.elements.append (AnchorElement (x, y))

    def close (self):
        self.closed = True

    def open (self):
        self.closed = False

    def setSVG (self):
        attr = Element.setSVG (self)
        elements = deepcopy (self.elements)
        self.applyTransform (*elements)
        strings = map (str, elements)
        if self.closed:
            strings.append (str (CloseElement ()))
        attr.update ([('d', ' '.join (strings)), ('transform', self.postTransform)])
        return attr
        

class CDATAPath (Element):
    def __init__ (self, **attr):
        Element.__init__ (self, name='path', **attr)
        if attr.has_key ('data'):
            self.data = attr['data']
        else:
            self.data = None
        if attr.has_key ('transform'):
            self.postTransform = attr['transform']
        else:
            self.postTransform = None

    def setSVG (self):
        attr = Element.setSVG (self)
        attr.update ([('d', self.data), ('transform', self.postTransform)])
        return attr


class Rectangle (BoxElement):
    def __init__ (self, **attr):
        BoxElement.__init__ (self, name = 'rect', **attr)
        if attr.has_key ('width'):
            self.width = float (attr['width'])
        else:
            self.width = None
        if attr.has_key ('height'):
            self.height = float (attr['height'])
        else:
            self.height = None
        if attr.has_key ('absoluteSize'):
            self.absoluteSize = bool (attr['absoluteSize'])
        else:
            self.absoluteSize = False
        if attr.has_key ('worldDeltaX'):
            self.worldDeltaX = float (attr['worldDeltaX'])
        else:
            self.worldDeltaX = 0.0
        if attr.has_key ('worldDeltaY'):
            self.worldDeltaY = float (attr['worldDeltaY'])
        else:
            self.worldDeltaY = 0.0
        
    def setSVG (self):
        attr = BoxElement.setSVG (self)
        if not self.absoluteSize:
            points = self.calulateBox (self.x, self.y, self.width, self.height)
        else:
            point = V (self.x, self.y)
            self.applyTransform (point)
            points = {'x': point.x, 'y': point.y,
                      'width': self.width, 'height': self.height}
        points['x'] += self.worldDeltaX
        points['y'] += self.worldDeltaY
        attr.update (points)
        return attr

class Square (Rectangle):
    def __init__ (self, width, **attr):
        attr.update ([('width', width), ('height', width)])
        Rectangle.__init__ (self, **attr)

    def size (self, value):
        self.width = value
        self.height = value


class Line (PositionableElement):
    def __init__ (self, **attr):
        PositionableElement.__init__ (self, name = 'line', **attr)
        if attr.has_key ('point1'):
            self.point1 = V (*attr['point1'])
        else:
            self.point1 = V (0.0, 0.0)
        if attr.has_key ('point2'):
            self.point2 = V (*attr['point2'])
        else:
            self.point2 = V (0.0, 0.0)

    def setSVG (self):
        attr = PositionableElement.setSVG (self)
        point1 = V (self.point1.x + self.x, self.point1.y + self.y)
        point2 = V (self.point2.x + self.x, self.point2.y + self.y)
        self.applyTransform (point1, point2)
        attr.update ([('x1', point1.x),
                      ('y1', point1.y),
                      ('x2', point2.x),
                      ('y2', point2.y)])
        return attr


class Sector (PositionableElement):
    def __init__ (self, radius, start, delta, **attr):
        PositionableElement.__init__ (self, name = 'path', **attr)
        self.radius = radius
        if delta < 0:
            delta = -delta
            start -= delta
        self.point1 = self.arcPoint (start)
        self.point2 = self.arcPoint (start + delta)

    def arcPoint (self, rads):
        x = self.radius * cos (rads)
        y = self.radius * sin (rads)
        return V (x, y)

    def setSVG (self):
        attr = PositionableElement.setSVG (self)
        pos = V (self.x, self.y)
        o = pos
        p1 = self.point1 + pos
        p2 = self.point2 + pos
        self.applyTransform (o, p1, p2)
        d1 = 'M ' + str (o)
        d2 = 'L ' + str (p1)
        d3 = 'A ' + str(self.radius) + ' ' + str(self.radius) + ' 1 0 0 '
        d3 += str(p2)
        d4 = 'Z'
        data = ' '.join ([d1, d2, d3, d4])
        attr.update ([('d', data)])
        return attr

class Text (Grouping, PositionableElement):
    def __init__ (self, **attr):
        Grouping.__init__ (self, **attr)
        PositionableElement.__init__ (self, **attr)
        if attr.has_key ('text'):
            self.text = attr['text']
        else:
            self.text = ''
        if attr.has_key ('textHeight'):
            self.textHeight = attr['textHeight']
        else:
            self.textHeight = 10
        if attr.has_key ('verticalAnchor'):
            self.verticalAnchor = attr['verticalAnchor']
        else:
            self.verticalAnchor = 'top'
        if attr.has_key ('horizontalAnchor'):
            self.horizontalAnchor = attr['horizontalAnchor']
        else:
            self.horizontalAnchor = 'left'
        self.width = 0
        self.height = 0
        self.createText ()

    def createText (self):
        xpos = self.x
        for char in self.text:
            if LetterDict.has_key (char):
                letter = LetterDict[char]
                id = char
                s = Symbol (id = id, viewBox = ViewBox (0, -800, letter[0], 250))
                p = CDATAPath (data=letter[1], transform = 'scale(1,-1)')
                p.style.strokeColor = 'black'
                s.draw (p)
                self.createDef (s)
                w = self.textHeight * (letter[0] / 1050.0)
                self.draw (Letter (href = ('#' + id), 
                                   x = xpos, 
                                   y = self.y, 
                                   width = w, 
                                   height = self.textHeight))
                xpos += w
            else:
                xpos += self.textHeight * (300.0 / 1050.0)
        self.width = xpos - self.x
        self.height = self.textHeight
        self.applyAnchors ()

    def move (self, dx, dy):
        for char in self:
            char.x += dx
            char.y += dy

    def applyAnchors (self):
        dh = 0
        hv = 0
        if self.horizontalAnchor == 'left':
            dh = 0
        elif self.horizontalAnchor == 'right':
            dh = - self.width
        elif self.horizontalAnchor == 'center':
            dh = - (self.width / 2.0)

        if self.verticalAnchor == 'top':
            dv = 0
        elif self.verticalAnchor == 'bottom':
            dv = - self.height
        elif self.verticalAnchor == 'middle':
            dv = - (self.height / 2.0)

        for char in self:
            char.dh += dh
            char.dv += dv

    def setText (self, text):
        self.clear ()
        self.text = text
        self.createText ()

    @staticmethod
    def textWidth (text, height):
        width = 0.0
        for char in text:
            if LetterDict.has_key (char):
                w = LetterDict[char][0]
                letterWidth = height * (w / 1050.0)
                width += letterWidth
            else:
                width += height * (300.0 / 1050.0)
        return width


class Letter (Use):
    def __init__ (self, **attr):
        Use.__init__ (self, **attr)
        if attr.has_key ('dh'):
            self.dh = attr['dh']
        else:
            self.dh = 0
        if attr.has_key ('dv'):
            self.dv = attr['dv']
        else:
            self.dv = 0

    def setSVG (self):
        p = V (self.x, self.y)
        self.applyTransform (p)
        return {'x': p.x + self.dh,
                'y': p.y + self.dv,
                'width': self.width,
                'height': self.height,
                'xlink:href': self.href,
                }


LetterDict = {
"!": (278,"M208 729V391L186 168H147L125 391V729H208ZM208 104V0H124V104H208Z"),
"#": (556,"M485 697L449 501H542V433H436L405 259H510V191H393L354 -20H278L316 191H192L153 -20H77L115 191H14V259H128L159 433H51V501H172L208 697H284L248 501H373L408 697H485ZM360 433H236L204 259H329L360 433Z"),
"$": (556,"M518 195Q518 99 463 42T302 -23V-126H243V-23Q142 -16 88 39T33 191V208H112Q114 188 114 182T118 157T124 131T134 108T150 86T172 69T203 55T243 46V318Q150 346 117 370Q46 421 46 516Q46 601 96 652T243 716V770H302V716Q393 709 444 657T496 519H417Q416 574 384 609T302 646V397Q306 396 332 389T372 377T411 361T452 337T485 304T510 256T518 195ZM243 405V645Q187 637 157 606T127 526Q127 436 243 405ZM302 46Q369 54 402 91T436 183Q436 232 408 259T302 309V46Z"),
"%": (889,"M199 685Q271 685 320 635T370 512Q370 443 320 393T200 343T80 393T29 514T79 634T199 685ZM199 615Q158 615 128 586T98 514Q98 473 128 443T200 413Q241 413 271 442T301 513Q301 556 272 585T199 615ZM609 709H675L280 -20H214L609 709ZM688 322Q760 322 809 272T859 150Q859 81 809 31T689 -19Q618 -19 568 31T518 152T568 272T688 322ZM688 252Q647 252 617 223T587 152Q587 110 617 81T689 51Q730 51 760 80T790 150Q790 193 761 222T688 252Z"),
"(": (333,"M236 729H291Q154 508 154 259Q154 11 291 -212H236Q161 -114 117 13T73 259T117 504T236 729Z"),
")": (333,"M93 -212H38Q175 9 175 258Q175 506 38 729H93Q168 631 212 504T256 258T212 13T93 -212Z"),
"*": (389,"M160 729H223L218 617L324 655L343 596L235 566L305 477L254 441L192 534L129 441L79 477L148 566L40 596L59 655L165 617L160 729Z"),
"+": (584,"M534 267V197H327V-10H257V197H50V267H257V474H327V267H534Z"),
",": (278,"M87 104H192V-16Q192 -147 87 -147V-109Q122 -108 134 -89T147 -18V0H87V104Z"),
"-": (333,"M284 312V240H46V312H284Z"),
".": (278,"M191 104V0H87V104H191Z"),
"/": (278,"M229 729H284L47 -20H-8L229 729Z"),
"0": (556,"M43 343Q43 432 58 500T96 606T151 669T212 701T275 709Q507 709 507 337Q507 162 448 70T275 -23Q161 -23 102 70T43 343ZM417 631T275 631T133 342Q133 50 273 50Q347 50 382 122T417 345Q417 631 275 631Z"),
"1": (556,"M259 505H102V568Q204 581 235 604T289 709H347V0H259V505Z"),
"2": (556,"M50 463Q57 709 284 709Q385 709 448 651T511 501Q511 369 361 287L261 233Q196 198 168 165T133 87H506V0H34Q40 117 81 180T233 307L325 359Q421 414 421 499Q421 556 381 594T281 632Q148 632 138 463H50Z"),
"3": (556,"M270 632Q194 632 166 591T135 480H47Q52 709 269 709Q370 709 427 657T485 514Q485 406 386 367Q450 345 478 306T506 198Q506 97 441 37T266 -23Q48 -23 32 206H120Q125 129 161 92T269 55Q338 55 377 92T416 197Q416 326 269 326L232 325H221V400Q316 402 355 424T395 511Q395 567 362 599T270 632Z"),
"4": (556,"M327 170H28V263L350 709H415V249H520V170H415V0H327V170ZM327 249V559L105 249H327Z"),
"5": (556,"M476 709V622H181L153 424Q212 467 284 467Q386 467 449 402T513 231Q513 119 445 48T270 -23Q229 -23 195 -14T138 7T97 40T69 76T51 115T40 148T35 174H123Q154 55 268 55Q340 55 381 99T423 219Q423 298 381 343T268 389Q227 389 198 375T138 323H57L110 709H476Z"),
"6": (556,"M43 323Q43 417 60 488T102 601T163 667T230 701T297 709Q378 709 431 660T498 524H410Q399 575 368 603T291 631Q215 631 175 562T133 362Q191 441 296 441Q391 441 452 378T513 216Q513 112 448 45T281 -23Q43 -23 43 323ZM285 363Q220 363 179 322T138 214Q138 146 179 101T282 55Q343 55 383 98T423 209Q423 280 386 321T285 363Z"),
"7": (556,"M520 709V635Q400 475 331 323T232 0H138Q178 175 240 308T429 622H46V709H520Z"),
"8": (556,"M391 373Q513 315 513 196Q513 99 447 38T275 -23T104 38T37 197Q37 315 158 373Q104 407 83 439T62 520Q62 603 121 656T275 709T428 656T488 520Q488 470 467 438T391 373ZM331 631T275 631T186 601T152 519Q152 469 185 439T275 408Q330 408 364 438T398 518Q398 570 365 600ZM341 334T275 334T168 296T127 195T167 94T273 55Q340 55 381 93T423 195Q423 257 382 295Z"),
"9": (556,"M509 363Q509 269 492 198T450 85T389 19T321 -15T254 -23Q173 -23 120 26T53 162H141Q152 111 183 83T260 55Q336 55 376 124T418 324Q352 245 256 245T99 308T38 470Q38 574 103 641T270 709Q509 709 509 363ZM269 632Q208 632 168 588T128 477Q128 406 165 365T266 323T371 365T413 472Q413 541 372 586T269 632Z"),
":": (278,"M214 104V0H110V104H214ZM214 524V420H110V524H214Z"),
";": (278,"M215 524V420H111V524H215ZM110 104H215V-16Q215 -147 110 -147V-109Q145 -108 157 -89T170 -18V0H110V104Z"),
"=": (584,"M534 353V283H50V353H534ZM534 181V111H50V181H534Z"),
"?": (556,"M509 549Q509 503 491 466T446 405T394 358T349 307T330 246V199H240V254Q240 291 258 324T303 381T356 429T400 483T419 549Q419 600 384 631T291 663Q218 663 190 622T162 507H77Q77 622 132 681T296 741Q393 741 451 689T509 549ZM330 104V0H240V104H330Z"),
"@": (1015,"M665 501H748L658 221Q646 186 646 171Q646 153 661 140T696 127Q760 127 812 198T864 357Q864 482 760 573T512 664Q354 664 237 547T119 273Q119 130 227 33T494 -65Q573 -65 687 -33L715 -100Q603 -142 489 -142Q365 -142 260 -89T95 57T34 258Q34 356 76 450T192 612Q258 672 347 706T525 741Q700 741 825 631T951 369Q951 246 865 146Q789 57 679 57Q583 57 569 134Q503 62 427 62Q357 62 311 114T264 245Q264 354 342 438T521 522Q605 522 643 435L665 501ZM453 126Q518 126 563 209T609 368Q609 406 582 432T515 458Q452 458 403 393T354 244Q354 195 383 161T453 126Z"),
"A": (667,"M474 219H193L116 0H17L277 729H397L653 0H549L474 219ZM448 297L336 629L216 297H448Z"),
"B": (667,"M623 208Q623 114 564 57T408 0H79V729H375Q436 729 481 711T548 664T581 605T591 544Q591 432 490 385Q560 358 591 316T623 208ZM498 415T498 531T352 647H172V415H352Q498 415 498 531ZM399 82Q448 82 479 103T520 151T530 207Q530 264 496 298T399 333H172V82H399Z"),
"C": (722,"M48 356Q48 406 56 455T89 557T148 649T244 715T381 741Q619 741 662 503H567Q551 581 504 620T370 659Q264 659 203 578T141 357Q141 220 205 140T378 59Q468 59 516 109T581 266H677Q644 -23 377 -23Q302 -23 243 2T148 67T89 158T57 259T48 356Z"),
"D": (722,"M89 0V729H370Q509 729 588 632T667 365T588 98T370 0H89ZM182 82H354Q462 82 518 154T574 364Q574 503 518 575T354 647H182V82Z"),
"E": (667,"M183 332V82H613V0H90V729H595V647H183V414H580V332H183Z"),
"F": (611,"M183 332V0H90V729H579V647H183V414H531V332H183Z"),
"G": (778,"M137 362Q137 324 144 286T169 205T215 132T291 80T398 59Q498 59 562 122T627 283V303H405V385H709V-4H650L627 93Q523 -23 378 -23Q230 -23 137 83T44 357Q44 405 53 453T87 555T149 648T250 714T394 741Q519 741 599 680T699 508H604Q589 578 533 618T393 659Q277 659 207 578T137 362Z"),
"H": (722,"M551 332H176V0H83V729H176V414H551V729H644V0H551V332Z"),
"I": (278,"M194 729V0H100V729H194Z"),
"J": (500,"M221 55Q285 55 309 97T333 216V729H426V182Q426 87 371 32T220 -23Q126 -23 72 29T17 170V234H112V187Q112 123 140 89T221 55Z"),
"K": (667,"M172 255V0H79V729H172V360L535 729H655L358 432L658 0H548L291 374L172 255Z"),
"L": (556,"M173 729V82H533V0H80V729H173Z"),
"M": (833,"M468 0H370L163 611V0H75V729H204L420 94L632 729H761V0H673V611L468 0Z"),
"N": (722,"M646 729V0H541L164 591V0H76V729H177L558 133V729H646Z"),
"O": (778,"M742 353Q742 191 646 84T390 -23Q232 -23 135 82T38 359T135 635T389 741Q549 741 645 635T742 353ZM389 659Q273 659 202 577T131 359T202 142T390 59T577 141T649 355Q649 493 578 576T389 659Z"),
"P": (667,"M617 515Q617 422 561 366T413 309H184V0H91V729H392Q500 729 558 674T617 515ZM184 391H378Q445 391 482 425T520 519T483 613T378 647H184V391Z"),
"Q": (778,"M733 -1L686 -59L581 28Q495 -23 390 -23Q232 -23 135 82T38 359T135 635T390 741Q547 741 644 636T742 361Q742 189 639 76L733 -1ZM481 205L570 132Q649 221 649 360Q649 494 578 576T390 659T203 577T131 359T202 142T389 59Q449 59 509 87L435 149L481 205Z"),
"R": (722,"M536 360Q568 346 589 327T620 284T633 239T636 189Q636 180 636 163T635 138Q635 97 644 69T679 23V0H566Q546 46 546 119V184Q546 251 517 282T426 314H186V0H93V729H429Q536 729 593 679T651 534Q651 472 624 431T536 360ZM554 521Q554 593 516 620T411 647H186V396H411Q485 396 519 426T554 521Z"),
"S": (667,"M342 59Q398 59 437 72T494 106T520 147T528 191Q528 274 394 309L213 357Q70 394 70 527Q70 626 139 683T329 741Q455 741 525 682T596 515H508Q507 586 460 624T326 663Q252 663 208 629T163 540Q163 498 190 474T283 432L466 383Q540 363 580 315T621 200Q621 171 614 143T586 84T535 30T453 -8T336 -23Q295 -23 258 -17T181 7T114 52T68 126T48 232H136V227Q136 196 145 169T176 116T240 75T342 59Z"),
"T": (611,"M354 647V0H261V647H21V729H593V647H354Z"),
"U": (722,"M552 729H645V217Q645 107 569 42T364 -23Q234 -23 160 41T85 217V729H178V217Q178 138 228 99T364 59Q452 59 502 101T552 217V729Z"),
"V": (667,"M392 0H292L30 729H130L344 112L546 729H645L392 0Z"),
"W": (944,"M744 0H642L474 599L311 0H209L22 729H126L263 137L425 729H525L691 137L825 729H929L744 0Z"),
"X": (667,"M391 374L649 0H534L335 304L135 0H22L280 374L38 729H151L338 443L526 729H637L391 374Z"),
"Y": (667,"M387 286V0H294V286L13 729H128L342 374L550 729H661L387 286Z"),
"Z": (611,"M581 729V645L145 82H583V0H28V82L466 647H56V729H581Z"),
"[": (278,"M250 729V657H147V-140H250V-212H64V729H250Z"),
"\\": (278,"M47 729L284 -20H229L-8 729H47Z"),
"]": (277,"M22 -212V-140H125V657H22V729H208V-212H22Z"),
"^": (469,"M197 709H270L425 329H356L234 629L113 329H44L197 709Z"),
"_": (556,"M578 -126V-176H-22V-126H578Z"),
"`": (333,"M135 740L231 592H171L22 740H135Z"),
"a": (556,"M65 369Q71 539 275 539Q372 539 422 503T472 396V88Q472 47 517 47Q526 47 535 49V-14Q500 -23 478 -23Q438 -23 418 -5T392 54Q308 -23 214 -23Q135 -23 89 19T42 132Q42 155 46 174T56 207T76 234T99 255T131 270T166 281T208 290T252 297T302 304Q351 310 370 323T389 362V384Q389 422 359 442T272 462Q214 462 184 440T149 369H65ZM232 50Q301 50 345 86T389 165V259Q364 247 314 239T226 225T159 197T129 134T156 72T232 50Z"),
"b": (556,"M54 729H137V453Q194 539 299 539Q403 539 463 465T523 264Q523 134 461 56T295 -23Q188 -23 129 67V0H54V729ZM283 461Q217 461 177 406T137 258T177 111T283 55Q351 55 393 110T436 255Q436 349 395 405T283 461Z"),
"c": (500,"M471 348H387Q379 403 347 432T263 462Q195 462 157 407T118 253Q118 160 157 107T265 54Q372 54 393 180H477Q469 84 413 31T263 -23Q156 -23 94 51T31 253Q31 383 94 461T264 539Q355 539 409 490T471 348Z"),
"d": (556,"M495 729V0H421V69Q387 20 348 -1T254 -23Q148 -23 87 53T26 263Q26 388 87 463T251 539Q359 539 412 458V729H495ZM265 461Q197 461 155 405T113 258Q113 166 155 111T266 55Q332 55 372 110T412 256Q412 350 372 405T265 461Z"),
"e": (556,"M513 234H127Q128 162 155 122Q198 54 281 54Q383 54 418 159H502Q486 73 427 25T278 -23Q168 -23 104 51T40 255T105 461T280 539Q354 539 410 502T492 401Q513 346 513 234ZM129 302H423Q424 304 424 308Q424 373 382 417T279 462Q216 462 175 419T129 302Z"),
"f": (278,"M258 524V456H171V0H88V456H18V524H88V613Q88 669 120 700T211 732Q234 732 258 727V658Q239 659 229 659Q171 659 171 606V524H258Z"),
"g": (556,"M245 -23Q153 -23 91 52T29 253Q29 381 90 460T252 539Q350 539 412 448V524H489V86Q489 11 480 -39T447 -133T376 -197T255 -218Q163 -218 108 -176T46 -60H131Q145 -148 258 -148Q342 -148 373 -101T404 44V71Q369 21 332 -1T245 -23ZM261 462Q194 462 155 407T116 258Q116 163 155 109T262 54Q328 54 366 107T404 255Q404 353 367 407T261 462Z"),
"h": (556,"M403 363Q403 418 370 442T295 466Q231 466 192 418T153 289V0H70V729H153V452Q190 500 227 519T321 539Q397 539 441 501T486 396V0H403V363Z"),
"i": (222,"M150 518V-6H67V518H150ZM150 729V624H66V729H150Z"),
"j": (222,"M70 524H153V-109Q153 -218 10 -218Q-3 -218 -18 -215V-144Q-7 -145 2 -145Q40 -145 55 -130T70 -76V524ZM153 729V624H70V729H153Z"),
"k": (500,"M141 729V302L363 524H470L288 343L502 0H399L222 284L141 204V0H58V729H141Z"),
"l": (222,"M152 729V0H68V729H152Z"),
"m": (833,"M70 524H147V450Q181 497 218 518T308 539Q405 539 449 459Q486 503 522 521T610 539Q683 539 722 502T762 393V0H678V361Q678 411 653 438T581 466Q530 466 494 426T458 329V0H374V361Q374 411 349 438T277 466Q226 466 190 426T154 329V0H70V524Z"),
"n": (556,"M70 524H147V436Q182 491 222 515T321 539Q397 539 442 500T487 396V0H404V363Q404 410 375 438T296 466Q232 466 193 418T154 289V0H70V524Z"),
"o": (556,"M272 539Q385 539 447 465T510 254Q510 125 447 51T273 -23Q161 -23 99 51T36 258T99 464T272 539ZM273 462Q203 462 163 408T123 258T163 109T273 54Q342 54 382 108T423 255Q423 352 384 407T273 462Z"),
"p": (556,"M54 -218V524H131V445Q190 539 298 539Q402 539 462 462T523 253Q523 128 462 53T299 -23Q202 -23 138 55V-218H54ZM284 461Q218 461 178 406T138 258T178 111T284 55Q352 55 394 110T436 255Q436 349 395 405T284 461Z"),
"q": (556,"M495 -218H412V60Q355 -23 250 -23Q146 -23 86 51T26 252Q26 382 88 460T254 539Q361 539 421 454V524H495V-218ZM266 461Q197 461 155 405T113 258Q113 166 155 111T266 55Q332 55 372 110T412 255Q412 349 373 405T266 461Z"),
"r": (333,"M321 451Q237 449 195 412T153 272V0H69V524H146V429Q182 488 215 513T289 539Q300 539 321 536V451Z"),
"s": (500,"M122 156Q128 109 154 82T250 54Q305 54 338 76T372 136Q372 165 353 182T291 209L213 228Q120 250 84 283T47 379Q47 452 102 495T248 539T388 497T438 378H350Q347 462 245 462Q194 462 164 441T134 383Q134 355 157 338T231 308L311 289Q389 270 424 236T459 143Q459 67 401 22T243 -23Q40 -23 34 156H122Z"),
"t": (278,"M254 524V456H168V97Q168 69 177 60T214 50Q239 50 254 54V-16Q215 -23 186 -23Q137 -23 111 -2T85 60V456H14V524H85V668H168V524H254Z"),
"u": (556,"M482 0H407V73Q370 21 330 -1T232 -23Q156 -23 111 16T65 120V524H148V153Q148 106 177 78T256 50Q321 50 360 98T399 227V524H482V0Z"),
"v": (500,"M285 0H194L10 524H104L244 99L392 524H486L285 0Z"),
"w": (722,"M554 0H459L353 411L252 0H158L6 524H98L205 116L305 524H407L510 116L614 524H708L554 0Z"),
"x": (500,"M292 271L473 0H376L245 201L112 0H17L202 267L27 524H122L248 334L374 524H468L292 271Z"),
"y": (500,"M388 524H478L245 -110Q204 -218 110 -218Q79 -218 54 -205V-130Q81 -136 98 -136Q124 -136 139 -125T165 -85L197 -2L20 524H109L243 116L388 524Z"),
"z": (500,"M443 524V450L132 73H457V0H31V75L344 451H52V524H443Z"),
"{": (334,"M276 729V664H261Q224 664 211 650T198 597V416Q198 347 180 312T116 259Q198 221 198 101V-80Q198 -119 211 -133T261 -147H276V-212H230Q178 -212 150 -178T121 -81V86Q121 155 104 185T43 224V293Q87 302 104 331T121 431V598Q121 660 149 694T230 729H276Z"),
"|": (260,"M100 729H160V-212H100V729Z"),
"}": (334,"M29 -212V-147H45Q82 -147 95 -133T109 -80V101Q109 221 191 258Q109 296 109 416V597Q109 636 96 650T45 664H29V729H76Q128 729 157 695T186 598V431Q186 362 202 332T262 293V224Q219 215 203 185T186 86V-81Q186 -143 157 -177T76 -212H29Z"),
"~": (584,"M181 371Q134 371 128 293H75Q79 363 106 400T183 438Q210 438 237 422L354 353Q382 336 404 336Q434 336 444 354T455 411H508Q508 268 403 268Q364 268 322 294L224 357Q201 371 181 371Z")
}
