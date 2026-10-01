// 슬라이드 p3-v2-fixed-later — 움직이는 버퍼의 인덱싱, C# 7.3
using System;

unsafe struct Buf { public fixed int A[4]; }

class Holder { public Buf B; }           // inside a movable object

class App
{
    static unsafe void Main()
    {
        Holder h = new Holder();
        fixed (int* p = h.B.A)           // C# 2: pin first
        {
            p[1] = 5;
        }
        h.B.A[2] = 6;                    // C# 7.3: index directly
        Console.WriteLine(h.B.A[1] + " " + h.B.A[2]);
    }
}
