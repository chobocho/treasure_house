// probe
using System;

class Base
{
    public virtual string M<T>(T? x) where T : struct
    {
        return "Base " + x.HasValue;
    }
}

class Derived : Base
{
    public override string M<T>(T? x) where T : struct
    {
        return "Derived " + x.HasValue;
    }
}

class App
{
    static void Main()
    {
        Base b = new Derived();
        Console.WriteLine(b.M<int>(3));
    }
}
