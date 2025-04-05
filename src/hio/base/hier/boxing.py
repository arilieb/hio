# -*- encoding: utf-8 -*-
"""
hio.core.hier.boxing Module

Provides hierarchical box work support


"""
from __future__ import annotations  # so type hints of classes get resolved later


from ..tyming import Tymee
from ...hioing import Mixin, HierError
from .hiering import WorkDom, ActBase
from .acting import Act, Tract
from .needing import Need
from ...help import modify, Mine, Renam


class Box(Tymee):
    """Box Class for hierarchical action framework (boxwork) instances.
    Box instance holds reference to in-memory data mine shared by all the boxes in a
    given boxwork as well as its executing Boxer.
    Box instance holds references (links) to its over box and its under boxes.
    Box instance holds the acts to be executed in their context.

    Inherited Attributes, Properties
        see Tymee

    Attributes:
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork
        over (Box | None): this box's over box instance or None
        unders (list[Box]): this box's under box instances or empty
                            zeroth entry is primary under


        preacts (list[act]): precond (pre-conditions for entry) context acts
        remacts (list[act]): remark renter mark subcontext acts
        renacts (list[act]): renter (re-enter) context acts
        emacts (list[act]): emark enter mark subcontext acts
        enacts (list[act]):  enter context acts
        reacts (list[act]): recur context acts
        lacts (list[act]): last context acts
        tracts (list[act]): transit context acts
        exacts (list[act]): exit context acts
        rexacts (list[act]): rexit (re-exit) context acts

    Properties:
        name (str): unique identifier of instance
        pile (list[Box]): this box's pile of boxes generated by tracing .over up
                          and .unders[0] down if any. This is generated lazily.
                          To refresh call ._trace()
        trail (str): human friendly represetion of pile as delimited string of
                        box names from .pile. This is generated lazily.
                        To refresh call ._trace()

    Hidden:
        _name (str): unique identifier of instance
        _pile (list[Box] | None): pile of Boxes to which this box belongs.
                                  None means not yet traced.
        _spot (int | None): zero based offset into .pile of this box. This is
                            computed by ._trace
        _trail (int | None): human friendly represetion of pile as delimited
                             string of box names from .pile.
                            This is computed by ._trace
        _trace(): function to trace and update ._pile from .over and .unders[0]
                  and update ._spot and ._trail
        _next (Box | None): this box's next box if any lexically




    """
    def __init__(self, *, name='box', mine=None, dock=None, over=None, **kwa):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of box
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork
            over (Box | None): this box's over box instance or None
        """
        super(Box, self).__init__(**kwa)
        self.name = name
        self.mine = mine if mine is not None else Mine()
        self.dock = dock   # stub for now until create Dock class
        self._pile = None  # force .trace on first access of .pile property
        self._spot = None  # zero based offset into .pile of this box
        self._trail = None  # delimited string representation of box names in .pile
        self.over = over  # over box
        self.unders = []  # list of under boxes,

        # acts by contexts
        self.preacts = []  # precond context list of pre-entry acts
        self.remacts = []  # renter mark subcontext list of re-mark acts
        self.renacts = []  # renter context list of re-enter acts
        self.emacts = []  # enter mark subcontext list of e-mark acts
        self.enacts = []  # enter context list of enter acts
        self.reacts = []  # recur context list of recurring acts
        self.lacts = []  # last context list of last acts
        self.tracts = []  # transit context list of transition acts
        self.exacts = []  # exit context list of exit acts
        self.rexacts = []  # rexit context list of re-exit acts

        #lexical context
        self._next = None  # next box lexically


    def __repr__(self):
        """Representation usable by eval()."""
        return (f"{self.__class__.__name__}(name='{self.name}')")

    def __str__(self):
        """Representation human friendly."""
        return (f"{self.__class__.__name__}({self.trail})")


    def _trace(self):
        """Trace pile and update .pile by tracing over up if any and unders[0]
        down if any.
        """
        pile = []
        over = self.over
        while over:
            pile.insert(0, over)
            over = over.over
        pile.append(self)
        self._spot = len(pile) - 1
        under = self.unders[0] if self.unders else None
        while under:
            pile.append(under)
            under = under.unders[0] if under.unders else None
        self._pile = pile

        up = "<".join(over.name for over in self._pile[:self._spot])
        dn = ">".join(under.name for under in self._pile[self._spot+1:])
        self._trail = up + "<" + self._name + ">" + dn


    @property
    def name(self):
        """Property getter for ._name

        Returns:
            name (str): unique identifier of instance
        """
        return self._name


    @name.setter
    def name(self, name):
        """Property setter for ._name

        Parameters:
            name (str): unique identifier of instance
        """
        if not Renam.match(name):
            raise HierError(f"Invalid {name=}.")
        self._name = name


    @property
    def pile(self):
        """Property getter for ._pile

        Returns:
            pile (list[Box]): this box's pile of boxes generated by tracing
                              .over up and .unders[0] down if any. This is
                              generated lazily to refresh call ._trace().
                              pile always includes self once traced.
        """
        if self._pile is None:
            self._trace()
        return self._pile

    @property
    def spot(self):
        """Property getter for ._spot

        Returns:
            spot (int): zero based offset of this box into its pile of boxes
                        generated by tracing .over up and .unders[0] down if any.
                        This is generated lazily. To refresh call ._trace().
                        Since pile always includes self, spot is always defined
                        once traced.
        """
        if self._spot is None:
            self._trace()
        return self._spot

    @property
    def trail(self):
        """Property getter for ._trail

        Returns:
            trail (str): human frieldly delimited string of box names from .pile.
                        This is generated lazily. To refresh call ._trace().
                        Since pile always includes self, trail is always defined
                        once traced.
        """
        if self._trail is None:
            self._trace()
        return self._trail





class Boxer(Tymee):
    """Boxer Class that executes hierarchical action framework (boxwork) instances.
    Boxer instance holds reference to in-memory data mine shared by all its boxes
    and other Boxers in a given boxwork.
    Box instance holds a reference to its first (beginning) box.
    Box instance holds references to all its boxes in dict keyed by box name.

    Inherited Attributes, Properties
        see Tymee

    Attributes:
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork
        first (Box | None):  beginning box
        doer (Doer | None): doer running this boxer  (do we need this?)
        boxes (dict): all boxes mapping of (box name, box) pairs

        pile (list[Box]): active pile of boxes
        box (Box | None):  active box in pile

    Properties:
        name (str): unique identifier of instance

    Hidden:
        _name (str): unique identifier of instance


    Cycle Context Order

    Init:

    all tymes in bags are None from init
    all tyme in marks are None



    tyme = start tyme (default ) 0.0
    Prep:

        First box assigned to active box
        actives = active box.pile
        .renters is empty
        .enters == actives
        exits is empty
        rexits is empty

        for each box in enters top down:
            precond:
                if not all true then done with boxwork
                    return from Prep (used for .done True done False not done)

        for box in renters top down: (empty)
            remark renter mark subcontext
            renter
        for box in enters top down: (not empty)
            emark enter mark subcontext  (mark tyme set to bag._tyme which is None)
            enter
        Check for done complete stop of boxwork boxer.want stop desire stop
        for box in actives top down:
            recur
            after
            if transit need is true:  (short circuit recur of lower level boxes)
                compute renters enters exits rexits. save box.renters and box.enters
                for each box in enters (top down):
                    precond:
                        if not all true then do not proceed with transit return

                for box in exits bottom up:
                    exits
                for box in rexits bottom up:
                    rexits
                set new .active box
                return from prep False  (equiv of yield)


    tyme increment
    Run:
        for box in renters: (may be empty)
            remark renter mark subcontext
            renter
        for box in enters: (may be empty)
            emark enter mark subcontext  (mark tyme set to bag._tyme which is None)
            enter
        Check for done complete stop of boxwork boxer.want stop desire stop
        for box in actives top down:
            recur
            after
            if transit need is true:   (short circuit recur of lower level boxes)
                compute renters enters exits rexits,.
                    precond:
                        if not all true then do not proceed with transit return

                for box in exits bottom up:
                    exit
                for box in rexits bottom up:
                    rexit
                set new .active box
                return from run False  (equiv of yield)

    """
    def __init__(self, *, name='boxer', mine=None, dock=None, first=None,
                 doer=None, **kwa):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of box
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork
            first (Box | None):  beginning box
            doer (Doer | None): Doer running this Boxer doe we need this?


        """
        super(Boxer, self).__init__(**kwa)
        self.name = name
        self.mine = mine if mine is not None else Mine()
        self.dock = dock  # stub until create Dock class
        self.first = first
        self.doer = doer
        self.boxes = {}
        self.pile = []  # current active pile
        self.box = None  # current active box in active pile


    @property
    def name(self):
        """Property getter for ._name

        Returns:
            name (str): unique identifier of instance
        """
        return self._name


    @name.setter
    def name(self, name):
        """Property setter for ._name

        Parameters:
            name (str): unique identifier of instance
        """
        if not Renam.match(name):
            raise HierError(f"Invalid {name=}.")
        self._name = name

    def prep(self):
        """"""

    def run(self):
        """"""

    def quit(self):
        """"""


    def resolve(self):
        """Resolve both over box names and tract dest box names into boxes for
        all boxes in .boxes

        """
        for name, box in self.boxes.items():
            if isinstance(box.over, str):
                try:
                    over = self.boxes[over]  # resolve
                except KeyError as ex:
                    raise HierError(f"Unresolvable over box name={over} for"
                                           f"box {name=}.") from ex
                box.over = over  # resolve over as a box
                box.over.unders.append(box)  # add box to its over.unders list

            for tract in box.tracts:
                if isinstance(tract.dest, str):
                    if tract.dest == 'next':  # next
                        if not box._next:
                            HierError(f"Unresolvable dest 'next' for tract in "
                                      f"box{name=}")
                        dest = box._next
                    else:
                        try:
                            dest = self.boxes[tract.dest]  # resolve
                        except KeyError as ex:
                            raise HierError(f"Unresolvable dest box={tract.dest}"
                                f" for tract in box{name=}") from ex

                    tract.dest = dest  # resolve dest as box






    def make(self, fun):
        """Make box work for this boxer from function fun
        Parameters:
            fun (function):  employs be, do, on, go maker functions injected
                             works (boxwork state vars)

        def fun(bx):


        Injects works as WorkDom dataclass instance whose attributes are used to
        construct boxwork. WorkDom attributes include
            box (Box|None): current box in box work. None if not yet a box
            over (Box|None): current over Box in box work. None if top level
            bxpre (str): default name prefix used to generate unique box
                name relative to boxer.boxes
            bxidx (int): default box index used to generate unique box
                name relative to boxer.boxes


        """
        works = WorkDom()  # standard defaults
        bx = modify(mods=works)(self.bx)
        on = modify(mods=works)(self.on)
        go = modify(mods=works)(self.go)
        do = modify(mods=works)(self.do)
        fun(bx=bx, on=on, go=go, do=do)  # calling fun will build boxer.boxes
        self.resolve()
        return works  # for debugging analysis



    def bx(self, name: None|str=None, over: None|str|Box="",
                *, mods: WorkDom|None=None)->Box:
        """Make a box and add to box work

        Parameters:
            name (None | str): when None then create name from bepre and beidx
                               items in works.
                               if non-empty string then use provided
                               otherwise raise exception

            over (None | str | Box): over box for new box.
                                    when str then name of new over box
                                    when box then actual over box
                                    when None then no over box (top level)
                                    when empty then same level use _over

            mods (None | WorkDom):  state variables used to construct box work
                None is just to allow definition as keyword arg. Assumes in
                actual usage that mods is always provided as WorkDom instance of
                form:

                    box (Box|None): current box in box work. None if not yet a box
                    over (Box|None): current over Box in box work. None if top level
                    bxpre (str): default name prefix used to generate unique box
                        name relative to boxer.boxes
                    bxidx (int): default box index used to generate unique box
                        name relative to boxer.boxes



        """
        m = mods  # alias more compact

        if not name:  # empty or None
            if name is None:
                name = m.bxpre + str(m.bxidx)
                m.bxidx += 1
                while name in self.boxes:
                    name = m.bxpre + str(m.bxidx)
                    m.bxidx += 1

            else:
                raise HierError(f"Missing name.")

        if name in self.boxes:  # duplicate name
            raise HierError(f"Non-unique box {name=}.")

        if over is not None:  # not at top level
            if isinstance(over, str):
                if not over:  # empty string
                    over = m.over  # same level
                else:  # resolvable string
                    try:
                        over = self.boxes[over]  # resolve
                    except KeyError as ex:
                        raise HierError(f"Under box={name} defined before"
                                               f"its {over=}.") from ex

            elif over.name not in self.boxes:  # stray over box
                self.boxes[over.name] = over  # add to boxes

        box = Box(name=name, over=over, mine=self.mine, tymth=self.tymth)
        self.boxes[box.name] = box  # update box work
        if box.over is not None:  # not at top level
            box.over.unders.append(box)  # add to over.unders list

        m.over = over  # update current level
        if m.box:  # update last boxes lexical ._next to this box
            m.box._next = box
        m.box = box  # update current box
        return box


    def on(self, cond: None|str=None, key: None|str=None, expr: None|str=None,
                 *, mods: WorkDom|None=None, **kwa)->Need:
        """Make a special Need and return it.
        Used for special needs for tracts and also for beacts (before enter)

        Returns:
            need (Need):  newly created special need

        Parameters:
            cond (None|str): special need condition to be satisfied. This is
                resolved in evalable boolean expression.
                When None then ignore
                When str then special need condition to be resolved into evalable
                boolean expression

            key (None|str): key to mine item ref for special need cond when
                applicable, i.e. cond is with respect to mine at key that is
                not predetermined solely by cond. Otherwise None.
                When None use default for cond
                When str then resolve key to mine at key


            expr (None|str): evalable boolean expression as additional constraint(s)
                ANDed with result of cond.
                When None or empty then ignore
                When str then evalable python boolean expression to be ANDed with
                    the result of cond resolution.

            mods (None | WorkDom):  state variables used to construct box work
                None is just to allow definition as keyword arg. Assumes in
                actual usage that mods is always provided as WorkDom instance of
                form:

                    box (Box|None): current box in box work. None if not yet a box
                    over (Box|None): current over Box in box work. None if top level
                    bxpre (str): default name prefix used to generate unique box
                        name relative to boxer.boxes
                    bxidx (int): default box index used to generate unique box
                        name relative to boxer.boxes



        """
        m = mods  # alias more compact

        _expr = None

        if not cond:
            if not expr:
                cond = "updated"  # default
            else:  # no cond but with expr
                _expr = expr  # use expr instead of resolved cond
                expr = None  # can't have both _expr and expr same below

        if not _expr:  # cond above so need to resolve cond into _expr
            if cond == "updated":
                _expr = "True"
            else:
                pass  # raise error since must have valid _expr after here

        # now _expr is valid

        if expr:  # both resolved cond as _expr and expr so AND together
            _expr = "(" + _expr + ") and (" + expr + ")"



        need = Need(expr=_expr, mine=self.mine, dock=self.dock)


        return need




    def go(self, dest: None|str=None, expr: None|str=None,
                 *, mods: WorkDom|None=None, **kwa)->Tract:
        """Make a Tract and add it to the tracts context of the current box.

        Returns:
            tract (Tract):  newly created tract

        Parameters:
            dest (None|str|Box): destination box its name for transition.
                When None use next box if any
                When str then resolve name to box if possible else save for
                    later resolution
                When Box instance that already resolved

            expr (None|str): evalable boolean expression for transition to dest.
                When None then conditional always True. Always transit.
                When str then evalable python boolean expression to be
                    resolved into a Need instance for eval at run time

            mods (None | WorkDom):  state variables used to construct box work
                None is just to allow definition as keyword arg. Assumes in
                actual usage that mods is always provided as WorkDom instance of
                form:

                    box (Box|None): current box in box work. None if not yet a box
                    over (Box|None): current over Box in box work. None if top level
                    bxpre (str): default name prefix used to generate unique box
                        name relative to boxer.boxes
                    bxidx (int): default box index used to generate unique box
                        name relative to boxer.boxes



        """
        m = mods  # alias more compact

        if not dest or dest in ('next', 'Next', 'NEXT'):  # empty or None or next
            if m.box._next:
                dest = m.box._next
            else:
                dest = 'next'  # to be resolved later
        elif isinstance(dest, str):
            if not Renam.match(dest):
                raise HierError(f"Invalid {dest=}.")
            if dest in self.boxes:
                dest = self.boxes[dest]

        need = Need(expr=expr, mine=self.mine, dock=self.dock)

        tract = Tract(dest=dest, need=need)
        m.box.tracts.append(tract)
        return tract



    def do(self, deed: None|str=None, *, mods: WorkDom|None=None)->str:
        """Make an act and add to box work

        Parameters:
            deed (None | str):


            mods (None | WorkDom):  state variables used to construct box work
                None is just to allow definition as keyword arg. Assumes in
                actual usage that mods is always provided as WorkDom instance of
                form:

                    box (Box|None): current box in box work. None if not yet a box
                    over (Box|None): current over Box in box work. None if top level
                    bxpre (str): default name prefix used to generate unique box
                        name relative to boxer.boxes
                    bxidx (int): default box index used to generate unique box
                        name relative to boxer.boxes



        """
        m = mods  # alias more compact

        if not deed:  # empty or None
            if deed is None:
                deed = 'act' + str(m.bxidx)
                m.bxidx += 1
                while deed in self.boxes:
                    deed = 'act' + str(m.bxidx)
                    m.bxidx += 1

            else:
                raise HierError(f"Missing deed.")


        return deed


    @staticmethod
    def exen(near,far):
        """Computes the relative differences (uncommon  and common parts) between
        the box pile lists nears passed in and fars from box far.pile

        Parameters:
            near (Box): near box giving nears =near.pile in top down order
            far (Box): far box giving fars = far.pile in top down order.

        Assumes piles nears and fars are in top down order

        Returns:
            quadruple (tuple[list]): quadruple of lists of form:
                (exits, enters, renters, rexits) where:
                exits is list of uncommon boxes in nears but not in fars to be exited.
                    Reversed to bottom up order.
                enters is list of uncommon boxes in fars but not in nears to be entered
                rexits is list of common boxes in both nears and fars to be re-exited
                    Reversed to bottom up order.
                renters is list of common boxes in both nears and fars to be re-entered

                The sets of boxes in rexits and renters are the same set but rexits
                is reversed to bottum up order.


        Supports forced reentry transitions when far is in nears. This means fars
            == nears. In this case:
            The common part of nears/fars from far down is force exited
            The common part of nears/fars from far down is force entered

        When far in nears then forced entry at far so far is nears[i]
        catches that case for forced entry at some far in nears. Since
        far is in fars, then when far == nears[i] then fars == nears.

        Since a given box's pile is always traced up via its .over if any and down via
        its primary under i.e. .unders[0] if any, when far is in nears the anything
        below far is same in both fars and nears.

        Otherwise when far not in nears then i where fars[i] is not nears[i]
        indicates first box where fars down and nears down is uncommon i.e. the pile
        tree branches at i. This is the normal non-forced entry case for transition.

        Two different topologies are accounted for with this code.
        Recall that python slice of list is zero based where:
           fars[i] not in fars[:i] and fars[i] in fars[i:]
           nears[i] not in nears[:i] and nears[i] in nears[i:]
           this means fars[:0] == nears[:0] == [] empty list

        1.0 near and far in same tree either on same branch or different branches
            1.1 on same branch forced entry where nears == fars so far in nears.
               Walk down from shared root to find where far is nears[i]. Boxes above
               far given by fars[:i] == nears[:i] are re-exit re-enter set of boxes.
               Boxes at far and below are forced exit entry.
            1.2 on different branch to walk down from root until find fork where
               fars[i] is not nears[i]. So fars[:i] == nears[:i] above fork at i,
               and are re-exit and re-enter set of boxes. Boxes at i and below in
               nears are exit and boxes at i and below in fars are enter
        2.0 near and far not in same tree. In this case top of nears at nears[0] is
            not top of fars ar fars[0] i.e. different tree roots, far[0] != near[0]
            and fars[:0] == nears[:0] = [] means empty re-exits and re-enters and
            all nears are exit and all fars are entry.

        """
        nears = near.pile  # top down order
        fars = far.pile  # top down order
        l = min(len(nears), len(fars))  # l >= 1 since far in fars & near in nears
        for i in range(l):  # start at the top of both nears and fars
            if (far is nears[i]) or (fars[i] is not nears[i]): #first effective uncommon member
                # (exits, enters, rexits, renters)
                return (list(reversed(nears[i:])), fars[i:],
                        list(reversed(nears[:i])), fars[:i])




class Maker(Mixin):
    """Maker Class makes boxworks of Boxer and Box instances.
    Holds reference to in-memory mine shared by all boxes in boxwork
    Holds reference to current Boxer and Box being built

    ****Placeholder for now. Future to be able to make multiple boxers from
    single fun or in multiple iterations making.****

    Attributes:
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork
        boxer (Boxer | None): current boxer
        box (Box | None): cureent box

    Properties:
        name (str): unique identifier of instance

    Hidden:
        _name (str): unique identifier of instance

    """
    def __init__(self, *, name='maker', mine=None, dock=None, **kwa):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of instance
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork


        """
        super(Maker, self).__init__(**kwa)
        self.name = name
        self.mine = mine if mine is not None else Mine()
        self.dock = dock  # stub until create Dock class
        self.boxer = None
        self.box = None

    @property
    def name(self):
        """Property getter for ._name

        Returns:
            name (str): unique identifier of instance
        """
        return self._name


    @name.setter
    def name(self, name):
        """Property setter for ._name

        Parameters:
            name (str): unique identifier of instance
        """
        if not Renam.match(name):
            raise HierError(f"Invalid {name=}.")

        self._name = name

    def make(self, fun, mine=None, boxes=None):
        """Make box work from function fun
        Parameters:
            fun (function):  employs be, do, on, go maker functions with
                              globals
            bags (None|Mine):  shared data Mine for all made Boxers
            boxes (None|dict): shared boxes map



        """

        # bags, boxes, and boxers can be referenced by fun in its nonlocal
        # enclosing scope. collections references so do not need to be global
        mine = mine if mine is not None else Mine()  # create new if not provided
        boxes = boxes if boxes is not None else {}  # create new if not provided
        boxers = []  # list of made boxers

        # create a default boxer
        boxer = Boxer(name='boxer', mine=mine, boxes=boxes)
        boxers.append(boxer)

        fun()
