// 슬라이드 p12-v11-autodefault — 구조체 필드의 자동 기본값, C# 11
using System;

struct MagnitudeVector3d          // the proposal's example
{
    public double X, Y, Z;
    public double Magnitude = 1;
    public MagnitudeVector3d() { }
}

struct Celsius                    // validation lives in the setter
{
    double _v;
    public double Value
    {
        get => _v;
        set => _v = value >= -273.15 ? value
            : throw new ArgumentOutOfRangeException(nameof(value));
    }
    public Celsius(double v) { Value = v; }   // no "_v = default;"
}

class Program
{
    static void Main()
    {
        var m = new MagnitudeVector3d();
        Console.WriteLine("{0} {1} {2} | {3}", m.X, m.Y, m.Z,
            m.Magnitude);
        m.X = m.Y = m.Z = 2;
        Console.WriteLine(new Celsius(21.5).Value);
        try { new Celsius(-300); }
        catch (ArgumentOutOfRangeException e)
        {
            Console.WriteLine(e.GetType().Name + ": " + e.ParamName);
        }
    }
}
