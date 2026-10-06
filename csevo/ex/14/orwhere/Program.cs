// 슬라이드 p14-v13-or-where — 특성을 붙일 수 있는 곳과 없는 곳, C# 13
using System;
using P = System.Runtime.CompilerServices
    .OverloadResolutionPriorityAttribute;

class C
{
    [P(1)] public C() { }                     // constructor: ok
    [P(1)] public int this[int i] => i;       // indexer: ok
    [P(1)] public static void S() { }         // method: ok
#if OVR
    [P(1)] public override string ToString() => "C"; // override
#endif
#if PROP
    [P(1)] public int Prop => 0;              // non-indexer property
#endif
#if ACC
    public int this[long i] { [P(1)] get => 0; }  // accessor
#endif
#if CONV
    [P(1)] public static implicit operator int(C c) => 0;
#endif
#if FIN
    [P(1)] ~C() { }                           // finalizer
#endif
#if CCTOR
    [P(1)] static C() { }                     // static constructor
#endif
}

class Program
{
    static void Main()
    {
#if LAMBDA
        Action a = [P(1)] () => { };
#endif
#if LOCAL
        [P(1)] void Local() { }
        Local();
#endif
        Console.WriteLine(new C()[7]);
    }
}
