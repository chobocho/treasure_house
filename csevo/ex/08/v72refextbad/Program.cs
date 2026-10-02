// 슬라이드 p8-v7_2-refext-bad — ref·in 확장 메서드의 제약, C# 7.2
struct Vec { public double X; }

static class Ext
{
    public static void Clear(ref this string s) { }    // a class
    public static void Peek<T>(in this T x) { }        // in this T
    public static void Bump<T>(ref this T x)           // fine
        where T : struct { }
    public static void Scale(ref this Vec v) { v.X *= 2; }
}

class App
{
    static void Main()
    {
        int n = 1;
        n.Bump();                   // fine: n is a variable
    }
}
