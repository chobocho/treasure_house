// 슬라이드 p12-v11-sa-kinds — static abstract 로 요구하는 멤버, C# 11.0
using System;

interface IKinds<T> where T : IKinds<T>
{
    static abstract void Hello();                    // method
    static abstract int Count { get; set; }          // property
    static abstract event Action Changed;            // event
    static abstract T operator -(T x);               // operator
    static abstract bool operator ==(T a, T b);      // == and !=
    static abstract bool operator !=(T a, T b);
    static abstract implicit operator T(int v);      // conversions
    static abstract explicit operator int(T x);
#if BAD
    static abstract int Field;
#endif
}

struct N : IKinds<N>
{
    public int V;
    public static void Hello() => Console.WriteLine("hello N");
    public static int Count { get; set; }
    public static event Action Changed;
    public static N operator -(N x) => new N { V = -x.V };
    public static bool operator ==(N a, N b) => a.V == b.V;
    public static bool operator !=(N a, N b) => a.V != b.V;
    public static implicit operator N(int v) => new N { V = v };
    public static explicit operator int(N x) => x.V;
    public override bool Equals(object o) => o is N n && n.V == V;
    public override int GetHashCode() => V;
    public static void Raise() => Changed?.Invoke();
}

class App
{
    static void Use<T>() where T : IKinds<T>
    {
        T.Hello();
        T.Changed += () => Console.WriteLine("changed " + T.Count);
        T.Count = 7;
        T a = 5;                                     // implicit T(int)
        Console.WriteLine((int)(-a) + " " + (a == 5) + " " + (a != 5));
    }

    static void Main()
    {
        Use<N>();
        N.Raise();
    }
}
