// 슬라이드 p12-v11-rf-return — ref 필드는 ref 로 내줄 수 있다, C# 11
using System;

ref struct RS                         // the proposal's RS
{
    ref int _refField;
    int _field;

    public RS(ref int target) { _refField = ref target; _field = 7; }
    public ref int Prop1 => ref _refField;   // ok
#if BAD
    public ref int Prop2 => ref _field;      // this is scoped
#endif
    public int Field => _field;
}

class Program
{
    static ref int Pass(ref int x)
    {
        var rs = new RS(ref x);       // rs dies here, x does not
        return ref rs.Prop1;
    }
#if BAD2
    static ref int Leak()
    {
        int local = 0;
        var rs = new RS(ref local);
        return ref rs.Prop1;          // would point at a dead local
    }
#endif

    static void Main()
    {
        int v = 1;
        Pass(ref v) = 99;
        Console.WriteLine(v + " " + new RS(ref v).Field);
    }
}
