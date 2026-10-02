// 슬라이드 p8-v7-exprbody-bad — 식 본문이 될 수 없는 식, C# 7.0
class Box
{
    int v;

    public Box(int v) => v == 0;        // not a statement expression

    public int Value
    {
        get => v;
        set => value;                   // reads value, assigns nothing
    }

    public Box() : base() => v = 1;     // fine: initializer first
}

class App
{
    static void Main()
    {
    }
}
