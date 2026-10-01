// 슬라이드 p2-v1-valref — 값 형식과 참조 형식, C# 1.0
using System;

struct PointS { public int X; }
class PointC { public int X; }

class App
{
    static void Main()
    {
        PointS s1 = new PointS();
        PointS s2 = s1;          // copies the whole value
        s2.X = 5;
        Console.WriteLine("struct: s1.X=" + s1.X + " s2.X=" + s2.X);

        PointC c1 = new PointC();
        PointC c2 = c1;          // copies the reference
        c2.X = 5;
        Console.WriteLine("class:  c1.X=" + c1.X + " c2.X=" + c2.X);

        PointS[] arr = new PointS[2];
        arr[0].X = 7;            // element is a variable: in place
        PointS tmp = arr[1];
        tmp.X = 9;               // a copy: arr[1] unchanged
        Console.WriteLine("array:  " + arr[0].X + " " + arr[1].X);

        PointC[] refs = new PointC[2];
        Console.WriteLine("refs[0] null? " + (refs[0] == null));
    }
}
