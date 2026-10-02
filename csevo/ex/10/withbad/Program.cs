// 슬라이드 p10-v9-with-bad — with 가 거절되는 곳, C# 9.0
class Plain
{
    public int X { get; set; }
}

record R(int X)
{
    public int Y { get; }
}

class App
{
    static void Main()
    {
        var p = new Plain() with { X = 1 };  // not a record
        var r = new R(1);
        var s = r with { Y = 2 };            // get-only
#if STMT
        r with { X = 3 };                    // as a statement
#endif
    }
}
