// 슬라이드 p1-design-virt-cs — 같은 사고를 C# 1 에서, C# 1.0
using System;

class Derived : Base               // written against version 1
{
#if OVERRIDE
    public override void Foo()     // decided after reading
#else
    public virtual void Foo()      // as written for version 1
#endif
    {
        Console.WriteLine("Derived.Foo: deletes temp files");
    }
}

class Base                         // version 2 of the library
{
    public void Run()
    {
        Console.WriteLine("Base.Run");
        Foo();
    }
    public virtual void Foo()      // added in version 2
    {
        Console.WriteLine("Base.Foo: new hook in version 2");
    }
}

class Program
{
    static void Main()
    {
        new Derived().Run();
    }
}
