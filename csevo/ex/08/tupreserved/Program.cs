// 슬라이드 p8-v7-tuple-reserved — 쓸 수 없는 원소 이름, C# 7.0
class App
{
    static void Main()
    {
        var a = (Item2: 1, Item1: 2);   // ItemN only at position N
        var b = (Rest: 1, x: 2);        // a member of ValueTuple
        var c = (x: 1, x: 2);           // duplicate
        var d = (ToString: 1, y: 2);    // a member of ValueTuple
        var e = (Item1: 1, Item2: 2);   // fine: the right places
    }
}
