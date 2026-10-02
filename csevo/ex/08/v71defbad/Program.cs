// 슬라이드 p8-v7_1-default-bad — 대상 형식이 없는 default, C# 7.1
class App
{
    static void Main()
    {
        var x = default;                  // nothing to infer from
        const int c = default;            // fine: 0 is a constant
        const int? y = default;           // int? has no constants
        bool b = default == default;      // neither side has a type
        string s = default.ToString();    // no type to look up
        throw default;                    // null works, default not
    }
}
