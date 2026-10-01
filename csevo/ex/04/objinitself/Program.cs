// 슬라이드 p4-v3-objinit-self — 초기화자 안의 이름은 옛 객체, C# 3.0
using System;

class Range
{
    public int Low;
    public int High;
}

class App
{
    static void Main()
    {
        Range r = new Range { Low = 1, High = 2 };
        // r on the right side is still the OLD object:
        // the new one is stored into r only at the very end.
        r = new Range { Low = r.High, High = r.High + r.Low };
        Console.WriteLine(r.Low + ".." + r.High);

        // the same, written out with the hidden temporary
        Range s = new Range { Low = 1, High = 2 };
        Range tmp = new Range();
        tmp.Low = s.High;
        tmp.High = s.High + s.Low;
        s = tmp;
        Console.WriteLine(s.Low + ".." + s.High);
    }
}
