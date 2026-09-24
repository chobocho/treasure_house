module ex/05/prune

go 1.17

require example.com/a v1.0.0

require example.com/b v1.0.0 // indirect

replace (
	example.com/a => ./a
	example.com/b => ./b
)
