// 슬라이드 p10-v9-rec-forbid — 레코드에 쓸 수 없는 것, C# 9.0
class Base { }

record R1 : Base { }                     // record : class

record R2;

class C : R2 { }                         // class : record

record R3(int X)
{
    public static bool operator ==(R3 a, R3 b) => true;
    public static bool operator !=(R3 a, R3 b) => false;
    public R3 Clone() => this;
}

class App
{
    static void Main() { }
}
