# -*- encoding: utf-8 -*-
"""hio.core.hier.acting Module

Provides hierarchical action support

"""
from __future__ import annotations  # so type hints of classes get resolved later

from collections.abc import Callable
from collections import namedtuple

from ... import hioing
from ...hioing import Mixin, HierError
from ...help import Mine, Renam
from .hiering import Nabe, ActBase, register
from .needing import Need
from .bagging import Bag
from . import boxing




@register()
class Act(ActBase):
    """Act for do verb deeds as callables. At make (compile) time any callable
    that is available in the scope of the do verb in the boxer.make method
    can be passed in as the deed parameter and will be executed with ,iops as
    its parameters.

    do(deed, **iops)

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.
        Names (tuple[str]): tuple of aliases (names) under which this subclas
                            appears in .Registry. Created by @register

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.


    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act

    Inherited Attributes:
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

    Attributes:
        deed (Callable): action to be called with .iops as parameters else
                executable set of statements with M and D as locals

    Properties:
        compiled (bool): True means ._code holds compiled .deed
                         False means not yet compiled


    Hidden:

        _code (None|CodeType): compiled evalable boolean expression .expr
            None means not yet compiled from .expr


    Hidden
        _name (str|None): unique name of instance
        _iopts (dict): input-output-paramters for .act
        _nabe (str): action nabe (context) for .act
        _code (CodeType): compiled executable set of statements that execs .deed
            when it is a noncallable str.  M and D are in the locals of the exec.

    """
    Index = 0  # naming index for default names of this subclasses instances
    #Names = () tuple of aliases for this subclass created by @register



    def __init__(self, deed=None, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str|None): action nabe (context) for .act. Default is "endo"
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:
            deed (None|Callable):  callable to be actioned with iops

        """
        super(Act, self).__init__(**kwa)
        self.deed = deed if deed is not None else (lambda **iops: iops)
        self.iops.update(M=self.mine, D=self.dock)  # inject .mine and .dock
        self._code = None


    def act(self, **iops):  # passed in by call
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms for deed when deed is callable.


        """
        if callable(self.deed):
            return self.deed(**iops)

        if not self.compiled:  # not yet compiled so lazy
            self.compile()  # first time only recompile to ._code
        M = self.mine  # ensure M is in locals() for exec
        D = self.dock  # ensure D is in locals() for exec
        # note iops already in locals() for exec
        return exec(self._code)



    @property
    def compiled(self):
        """Property compiled

        Returns:
            compiled (bool): True means ._code holds compiled ._expr
                             False means not yet compiled
        """
        return True if self._code is not None else False


    def compile(self):
        """Compile evable boolean expression str ._expr into compiled code
        object ._code to be evaluated at run time.
        Because code objects are not pickleable the compilation must happen
        at prep (endo) time not init time.
        """
        self._code = compile(self.deed, '<string>', 'exec')




@register()
class Goact(ActBase):
    """Goact (go act) is subclass of ActBase whose .act evaluates conditional
    need expression to determine if a transition condition is satified for
    transition to its destination box.

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.
        Names (tuple[str]): tuple of aliases (names) under which this subclas
                            appears in .Registry. Created by @register

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.

    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act

    Inherited Attributes:
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

    Attributes:
        dest (Box): destination Box for this transition.
        need (Need): transition condition to be evaluated

    Hidden
        _name (str|None): unique name of instance
        _iops (dict): input-output-paramters for .act
        _context (str): action context for .act

    """
    Index = 0  # naming index for default names of this subclasses instances
    #Names = () tuple of aliases for this subclass created by @register



    def __init__(self, dest=None, need=None, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:
            dest (None|str|Box): destination Box for this transition.
                When None then resolve later to next box of current box
                When str is box name then resolve to box with that name
                When Box instance then use directly
            need (None|str|Need): transition condition to be evaluated
                When None then always evaluates to True
                When str = bool expression then create Need from expression
                When Need instance then use directly

        """
        kwa.update(nabe=Nabe.godo)  # override must be godo nabe
        super(Goact, self).__init__(**kwa)
        self.dest = dest if dest is not None else 'next'  # default is next
        self.need = need if need is not None else Need()  # default need evals to True
        if self.nabe != Nabe.godo:
            raise HierError(f"Invalid nabe='{self.nabe}' for Goact "
                            f"'{self.name}'")



    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        if self.need():
            if not isinstance(self.dest, boxing.Box):
                raise HierError(f"Unresolved dest={self.dest}")
            return self.dest
        else:
            return None


@register(names=('end', 'End'))
class EndAct(ActBase):
    """EndAct is subclass of ActBase whose .act indicates a desire to end the
    boxer by setting bag at .iops "end" .value to True. Where "end" is at key
    "_boxer_boxername_end".



    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.
        Names (tuple[str]): tuple of aliases (names) under which this subclas
                            appears in .Registry. Created by @register

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.


    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act

    Inherited Attributes:
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

    Attributes:

    Used iops:
        _boxer (str):  boxer name


    Hidden
        _name (str|None): unique name of instance
        _iops (dict): input-output-parameters for .act
        _nabe (str): action nabe (context) for .act

    """
    Index = 0  # naming index for default names of this subclasses instances

    def __init__(self, nabe=Nabe.endo, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb (do etc)


        """
        super(EndAct, self).__init__(nabe=nabe, **kwa)

        try:
            boxer = self.iops['_boxer']  # get boxer name
        except KeyError as ex:
            raise HierError(f"Missing iops '_boxer' for '{self.name}' instance "
                            f"of Act self.__class__.__name__") from ex


        keys = ("", "boxer", boxer, "end")  # _boxer_boxername_end
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag at end default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        keys = ("", "boxer", boxer, "end")
        self.mine[keys].value = True

# Dark  DockMark

@register()
class Mark(ActBase):
    """Mark (Mine Mark) is base classubclass of ActBase whose .act marks a mine bag for
    a special need condition.

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.
        Names (tuple[str]): tuple of aliases (names) under which this subclas
                            appears in .Registry. Created by @register

    Overridden Class Attributes
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.


    Inherited Properties:
        name (str): unique name string of instance
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act

    Inherited Attributes:
        mine (Mine): ephemeral bags in mine (in memory) shared by boxwork
        dock (Dock): durable bags in dock (on disc) shared by boxwork

    Attributes:
        bag (Bag): marked bag in Mine

    Used iops:
        _boxer (str):  boxer name
        _box (str): box name in boxer
        _key (str): marked bag key


    Hidden
        _name (str|None): unique name of instance
        _iopts (dict): input-output-paramters for .act
        _nabe (str): action nabe (context) for .act


    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabe.enmark, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb
            _key (str): marked bag key. Injected by on verb


        """
        super(Mark, self).__init__(nabe=nabe, **kwa)

        try:
            boxer = self.iops['_boxer']  # get boxer name
        except KeyError as ex:
            raise HierError(f"Missing iops '_boxer' for '{self.name}' instance "
                            f"of Act self.__class__.__name__") from ex

        try:
            box = self.iops['_box']  # get box name
        except KeyError as ex:
            raise HierError(f"Missing iops '_box' for '{self.name}' instance "
                            f"of Act self.__class__.__name__") from ex


        try:
            key = self.iops['_key']  # get bag key
        except KeyError as ex:
            raise HierError(f"Missing iops '_key' for '{self.name}' instance "
                            f"of Act self.__class__.__name__") from ex

        if key not in self.mine:
            raise HierError("Missing bag at '{key=}' for mark.")



    def act(self, **iops):
        """Act called by ActBase.

        Override in subclass

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        key = self.iops['_key']  # get marked bag key



@register()
class UpdateMark(Mark):
    """UpdateMark marks bag in mine for tyme update special need

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabe.enmark, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb
            _key (str): marked bag key. Injected by on verb


        """
        super(UpdateMark, self).__init__(nabe=nabe, **kwa)
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        key = self.iops['_key']  # get bag key in mine
        keys = ("", "boxer", boxer, "box", box, "update", key)
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag default value = None



    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']
        key = self.iops['_key']
        keys = ("", "boxer", boxer, "box", box, "update", key)
        # mark bag tyme
        self.mine[keys].value = self.mine[key]._tyme


@register()
class ChangeMark(Mark):
    """ChangeMark marks bag in mine for value change update special need
    Creates tuple of non-hidden fields in associated bag.

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabe.enmark, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb
            _key (str): marked bag key. Injected by on verb


        """
        super(ChangeMark, self).__init__(nabe=nabe, **kwa)
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']  # get box name
        key = self.iops['_key']  # get bag key in mine
        keys = ("", "boxer", boxer, "box", box, "change", key)
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']
        key = self.iops['_key']
        bag = self.mine[key]
        keys = ("", "boxer", boxer, "box", box, "change", key)
        self.mine[keys].value = bag._astuple()  # bag field value tuple as mark


@register()
class Count(ActBase):
    """Count tracks redo count of box in mine for count special need

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabe.redo, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb

        """
        super(Count, self).__init__(nabe=nabe, **kwa)

        try:
            boxer = self.iops['_boxer']  # get boxer name
        except KeyError as ex:
            raise HierError(f"Missing iops '_boxer' for '{self.name}' instance "
                            f"of Act self.__class__.__name__") from ex

        try:
            box = self.iops['_box']  # get box name
        except KeyError as ex:
            raise HierError(f"Missing iops '_box' for '{self.name}' instance "
                            f"of Act self.__class__.__name__") from ex

        keys = ("", "boxer", boxer, "box", box, "count")
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag default value = None



    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']
        keys = ("", "boxer", boxer, "box", box, "count")
        bag = self.mine[keys]  # count bag
        if bag.value is None:
            bag.value = 0  # start counter
        else:
            bag.value += 1  # inc counter


@register()
class Discount(ActBase):
    """Discount resets redo count to None of box in mine for count special need

    """
    Index = 0  # naming index for default names of this subclasses instances


    def __init__(self, nabe=Nabe.exdo, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action  nabe (context) for .act
            mine (None|Mine): ephemeral bags in mine (in memory) shared by boxwork
            dock (None|Dock): durable bags in dock (on disc) shared by boxwork

        Parameters:

        Used iops:
            _boxer (str): boxer name. Implicit iop injected by verb
            _box (str): box name in boxer.  Implicit iop injected by verb

        """
        super(Discount, self).__init__(nabe=nabe, **kwa)
        try:
            boxer = self.iops['_boxer']  # get boxer name
        except KeyError as ex:
            raise HierError(f"Missing iops '_boxer' for '{self.name}' instance "
                            f"of Act self.__class__.__name__") from ex

        try:
            box = self.iops['_box']  # get box name
        except KeyError as ex:
            raise HierError(f"Missing iops '_box' for '{self.name}' instance "
                            f"of Act self.__class__.__name__") from ex

        keys = ("", "boxer", boxer, "box", box, "count")
        if keys not in self.mine:
            self.mine[keys] = Bag()  # create bag default value = None


    def act(self, **iops):
        """Act called by ActBase.

        Parameters:
            iops (dict): input output parms

        """
        boxer = self.iops['_boxer']  # get boxer name
        box = self.iops['_box']
        keys = ("", "boxer", boxer, "box", box, "count")
        self.mine[keys].value = None  # reset count to None
