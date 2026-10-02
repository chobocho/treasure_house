// 슬라이드 p8-v7-pat-nullop — is null 은 == 를 부르지 않는다, C# 7.0
using System;

class Weird
{
    // a (bad) user-defined equality that says everything is null
    public static bool operator ==(Weird a, Weird b)
    {
        Console.WriteLine("  operator == called");
        return true;
    }
    public static bool operator !=(Weird a, Weird b) => !(a == b);
    public override bool Equals(object o) => base.Equals(o);
    public override int GetHashCode() => 0;
}

class App
{
    static void Main()
    {
        var w = new Weird();
        Console.WriteLine("w == null: " + (w == null));
        Console.WriteLine("w is null: " + (w is null));
        Console.WriteLine("(object)w == null: " + ((object)w == null));
    }
}
