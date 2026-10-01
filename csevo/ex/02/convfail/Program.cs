// 슬라이드 p2-v1-convfail — 사용자 변환은 한 번만 끼어든다, C# 1.0
using System;

struct Meter
{
    public double V;
    public static implicit operator Foot(Meter m)
    {
        Foot f; f.V = m.V * 3.28084; return f;
    }
}

struct Foot
{
    public double V;
    public static implicit operator Inch(Foot f)
    {
        Inch i; i.V = f.V * 12; return i;
    }
}

struct Inch { public double V; }

class App
{
    static void Main()
    {
        Meter m; m.V = 1;
        Foot f = m;                           // one user conversion
        Inch i = m;                           // would need two
        Console.WriteLine(f.V + " " + i.V);
    }
}
