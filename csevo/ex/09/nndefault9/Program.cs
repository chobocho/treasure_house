// 슬라이드 p9-v8-overcon-default — where T : default 는 C# 9, C# 9.0
#nullable enable
using System;

abstract class Base
{
    public abstract string M<T>(T? x) where T : struct;
    public abstract string M<T>(T? x);       // C# 9: T? on any T
}

class Derived : Base
{
    public override string M<T>(T? x) where T : struct => "struct";
    public override string M<T>(T? x) where T : default => "any";
}

class App
{
    static void Main()
    {
        Base b = new Derived();
        Console.WriteLine(b.M<int>(1) + " " + b.M<string>("s"));
    }
}
