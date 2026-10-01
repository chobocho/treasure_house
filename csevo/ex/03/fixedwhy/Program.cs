// 슬라이드 p3-v2-fixed-why — 배열 필드와 고정 크기 버퍼, C# 2.0
using System;
using System.Runtime.InteropServices;

struct WithMarshal                       // the C# 1 way for interop
{
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
    public int[] A;                      // in .NET: a reference
}

unsafe struct WithFixed { public fixed int A[4]; }   // inline

class App
{
    static unsafe void Main()
    {
        Console.WriteLine("marshalled: " + Marshal.SizeOf(
            typeof(WithMarshal)) + " and " +
            Marshal.SizeOf(typeof(WithFixed)));
        Console.WriteLine("sizeof(WithFixed) = " + sizeof(WithFixed));

        WithMarshal m = new WithMarshal();
        m.A = new int[4];
        WithMarshal m2 = m;              // copies the reference
        m2.A[0] = 5;
        Console.WriteLine("array field after copy: " + m.A[0]);

        WithFixed f = new WithFixed();
        WithFixed f2 = f;                // copies all 16 bytes
        f2.A[0] = 5;
        Console.WriteLine("fixed buffer after copy: " + f.A[0]);
    }
}
